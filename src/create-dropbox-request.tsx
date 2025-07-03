import React from "react";
import { Form, ActionPanel, Action, showToast, Toast, LaunchProps } from "@raycast/api";
import { useForm, FormValidation } from "@raycast/utils";
import { exec } from "child_process";
import { promisify } from "util";

const execAsync = promisify(exec);

// Hardcoded URL for the video progress page - USER MUST REPLACE THIS
const VIDEO_PROGRESS_PAGE_URL = "https://dashboard.nationalpid.com/videoteammsg/videomailprogress"; 

interface CreateDropboxRequestFormValues {
  athleteFullName: string;
  recipientEmail: string;
}

export default function CreateDropboxRequestCommand(props: LaunchProps<{ draftValues: CreateDropboxRequestFormValues }>) {
  const { handleSubmit, itemProps } = useForm<CreateDropboxRequestFormValues>({
    async onSubmit(formValues) {
      const toast = await showToast({
        style: Toast.Style.Animated,
        title: "Processing Dropbox request...",
      });

      try {
        const pythonInterpreter = "python3";
        // Using the absolute path you confirmed for the Python script
        const effectiveScriptPath = "/Users/singleton23/Desktop/RAYCAST/playerid-updates/automate_dropbox_and_email.py";

        const escapeShellArg = (arg: string | undefined): string => {
          if (arg === undefined || arg === null || arg === "") {
            return "''"; 
          }
          return `'${arg.replace(/'/g, "'\\\\''")}'`;
        };
        
        // Command construction simplified: always generate title from page
        const commandParts = [
          pythonInterpreter,
          escapeShellArg(effectiveScriptPath),
          '--athlete_full_name',
          escapeShellArg(formValues.athleteFullName),
          '--recipient_email',
          escapeShellArg(formValues.recipientEmail),
          '--generate_title_from_page', // Always pass this flag
          '--video_progress_page_url',
          escapeShellArg(VIDEO_PROGRESS_PAGE_URL) // Pass the hardcoded URL
        ];

        const command = commandParts.join(' ');

        await toast.show();
        toast.title = "Running automation script...";
        toast.message = "Browser will open. You may need to log into Dropbox if prompted.";

        console.log("Executing command:", command);
        const { stdout, stderr } = await execAsync(command, {
          shell: process.env.SHELL || "/bin/bash", 
        });

        console.log("Python script stdout:", stdout);
        
        if (stderr && (stderr.includes("ERROR") || stderr.includes("Traceback"))) {
          console.error("Python script stderr:", stderr);
          toast.style = Toast.Style.Failure;
          toast.title = "Automation Error";
          toast.message = stderr.substring(0, 250) + (stderr.length > 250 ? "..." : "");
          return;
        }

        if (stdout.includes("--- Dropbox Request Created and Email Sent Successfully ---")) {
          toast.style = Toast.Style.Success;
          toast.title = "Success!";
          toast.message = "Dropbox request created and email sent.";
        } else if (stdout.includes("--- Automation Script Finished ---")) {
          toast.style = Toast.Style.Success; 
          toast.title = "Script Finished";
          toast.message = "Python script completed. Check logs for details if outcome is not as expected.";
        } else {
          toast.style = Toast.Style.Failure;
          toast.title = "Script May Have Failed";
          toast.message = stdout.substring(0, 250) + (stdout.length > 250 ? "..." : "") || "Check console logs for details from the script.";
        }
      } catch (error: unknown) {
        console.error("Execution error:", error);
        toast.style = Toast.Style.Failure;
        toast.title = "Failed to Run Automation";
        if (error instanceof Error) {
          toast.message = error.message || "An unexpected error occurred.";
        } else {
          toast.message = "An unexpected error occurred.";
        }
        if (typeof error === "object" && error !== null) {
          if ("stdout" in error && (error as { stdout: unknown }).stdout) {
            console.error("Error stdout:", (error as { stdout: unknown }).stdout);
          }
          if ("stderr" in error && (error as { stderr: unknown }).stderr) {
            console.error("Error stderr:", (error as { stderr: unknown }).stderr);
          }
        }
      }
    },
    validation: {
      athleteFullName: FormValidation.Required,
      recipientEmail: (value) => {
        if (!value) return "Recipient email is required";
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) return "Please enter a valid email address";
        return undefined;
      },
    },
    initialValues: props.draftValues || {
      athleteFullName: "",
      recipientEmail: "",
    },
  });

  return (
    <Form
      enableDrafts
      actions={
        <ActionPanel>
          <Action.SubmitForm title="Create Request and Send Email" onSubmit={handleSubmit} />
        </ActionPanel>
      }
    >
      <Form.Description text="Enter athlete and recipient details to create a Dropbox file request and send a notification email. The Dropbox request title will be generated automatically from the video progress page. Note: If this is your first time using the tool, you may need to log into Dropbox when the browser opens." />
      <Form.Separator />

      <Form.TextField
        title="Athlete's Full Name"
        placeholder="Enter full name (e.g., Jane Doe)"
        {...itemProps.athleteFullName}
        autoFocus
      />
      <Form.TextField
        title="Recipient's Email Address"
        placeholder="Enter email for Dropbox link and notification"
        {...itemProps.recipientEmail}
      />
    </Form>
  );
} 