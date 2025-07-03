import React from "react";
import { Form, ActionPanel, Action, showToast, Toast, LaunchProps } from "@raycast/api";
import { useForm, FormValidation } from "@raycast/utils";
import { exec } from "child_process";
import { promisify } from "util";
import path from "path";
import { environment } from "@raycast/api";

const execAsync = promisify(exec);

// Interface for the Revisions form - only athleteName is needed from the form
interface RevisionsFormValues {
  athleteName: string;
  revisedYoutubeLink: string; // Removed the extraneous URL
}

// The main command function, named "RevisionsCommand"
export default function RevisionsCommand(props: LaunchProps<{ draftValues: RevisionsFormValues }>) {
  const { handleSubmit, itemProps, reset, focus } = useForm<RevisionsFormValues>({
    async onSubmit(formValues) {
      const toast = await showToast({
        style: Toast.Style.Animated,
        title: "Processing revisions...",
      });

      try {
        const pythonInterpreter = "python3";
        const scriptName = "process_revisions.py"; // Kept for reference, but path is now absolute
        const scriptPath = "/Users/singleton23/Desktop/RAYCAST/playerid-updates/process_revisions.py";
        
        const escapeShellArg = (str: string) => `"${str.replace(/"/g, '\"')}"`;

        const command = `${pythonInterpreter} ${escapeShellArg(scriptPath)} --athlete_name ${escapeShellArg(formValues.athleteName)} --revised_youtube_link ${escapeShellArg(formValues.revisedYoutubeLink)}`;

        await toast.show();
        toast.title = "Running Python automation for revisions...";
        toast.message = "Opening browser to process revisions. This may take a moment...";

        console.log("Executing command:", command);
        const { stdout, stderr } = await execAsync(command);

        console.log("Python script stdout:", stdout);
        
        if (stderr && stderr.includes("ERROR")) {
          console.error("Python script stderr:", stderr);
          toast.style = Toast.Style.Failure;
          toast.title = "Automation Error";
          toast.message = stderr.substring(0, 200) + (stderr.length > 200 ? "..." : "");
          return;
        }

        if (stdout.includes("--- Revisions Processed Successfully ---")) {
          toast.style = Toast.Style.Success;
          toast.title = "Revisions Processed Successfully";
          toast.message = "The revisions have been processed for the athlete's profile.";
          reset(); // Clear the form
        } else {
          toast.style = Toast.Style.Failure;
          toast.title = "Revision Processing May Have Failed";
          toast.message = stdout.includes("--- Revisions Script Finished") ? "Script finished, but revision success message not found. Check logs." : "Check the console logs for details.";
        }
      } catch (error: unknown) {
        console.error("Execution error:", error);
        toast.style = Toast.Style.Failure;
        toast.title = "Failed to Run Revisions Automation";
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
      athleteName: FormValidation.Required,
      revisedYoutubeLink: (value) => {
        if (!value) return "The revised YouTube link is required";
        if (!value.startsWith("https://www.youtube.com/") && !value.startsWith("https://youtu.be/")) {
          return "Please enter a valid YouTube link (e.g., https://www.youtube.com/watch?v=... or https://youtu.be/...)";
        }
        return undefined;
      },
    },
    initialValues: props.draftValues || {
      athleteName: "",
      revisedYoutubeLink: "",
    },
  });

  return (
    <Form
      enableDrafts
      actions={
        <ActionPanel>
          <Action.SubmitForm title="Submit and Process Revisions" onSubmit={handleSubmit} />
          <Action
            title="Focus Athlete Name"
            onAction={() => focus("athleteName")}
            shortcut={{ modifiers: ["cmd", "shift"], key: "a" }}
          />
          <Action
            title="Focus Revised YouTube Link"
            onAction={() => focus("revisedYoutubeLink")}
            shortcut={{ modifiers: ["cmd", "shift"], key: "l" }}
          />
        </ActionPanel>
      }
    >
      <Form.Description text="Enter the athlete's name and the revised YouTube link to process revisions on their video profile." />
      <Form.Separator />

      <Form.TextField
        title="Student Athlete's Name"
        placeholder="Enter full name"
        {...itemProps.athleteName}
        autoFocus
      />
      <Form.TextField
        title="Revised YouTube Link"
        placeholder="Enter the new YouTube link for the revision"
        {...itemProps.revisedYoutubeLink}
      />
    </Form>
  );
}