---
name: capture-reminders
description: Capture follow-up tasks into the macOS Reminders app via the apple-reminders MCP. Use when the user asks to remind them of something, at end-of-day to queue tomorrow's tasks, or when a manual step (something the agent cannot do itself) must be handed off to the user. Triggers on phrases like "remind me", "add a reminder", "wrap up the day", "end of day", "for tomorrow", or when a task requires the user to do something by hand.
---

# Capture Reminders

Turn actionable follow-ups into macOS reminders using the `apple-reminders` MCP
tools. The goal is to make sure nothing that requires the user's attention gets
lost between sessions.

## When to create a reminder

Create a reminder (proactively or on request) when one of these applies:

1. **Explicit request** — the user says "remind me", "add a reminder", "put
   this on my list", etc. Always honor these.
2. **End of working day** — when the user signals the day is wrapping up
   ("wrap up", "end of day", "that's it for today", "let's stop here"), offer to
   queue tasks for the next day: unfinished work, follow-ups, and anything that
   should be picked up tomorrow.
3. **Manual step required** — when completing a task depends on an action only
   the user can take (something outside the agent's reach), capture it so it
   isn't forgotten. Examples:
   - Approving/merging a PR, deploying, or running a release.
   - Rotating or entering a secret/credential the agent must not handle.
   - A physical or account action (call someone, sign a document, click a link
     in an email, grant a permission in a GUI).
   - Anything blocked on a human decision or external party.

Do NOT create reminders for trivial in-session steps you will complete yourself
moments later, or for purely informational notes.

## How to create a reminder

Use the `apple-reminders_create_reminder` tool.

- **name** (required): a short, action-oriented title. Start with a verb —
  "Merge PR #123", "Rotate API key", "Call vendor about invoice".
- **listName** (required): ALWAYS use `Work`. Do not ask the user which list or
  use any other list (e.g. `Tasks`, `Tech Tasks`) unless the user explicitly
  names a different list for a specific reminder.
- **body** (optional): context the user (or a future session) will need —
  repo/PR links, the exact command to run, or why the step is blocked.
- **Project tag** (when the reminder relates to a specific project/repo):
  ALWAYS include a machine-findable tag on its own line at the START of the
  body, in the exact form `[project:<name>]`. Use the repository/directory name
  as `<name>` (e.g. `apple-reminders-mcp`), lowercased, spaces replaced with
  hyphens. This is what makes project reminders retrievable later — do not skip
  it or vary the format.
  Example body:
  ```
  [project:apple-reminders-mcp]
  Commit the AppleScript injection fix; still only in the working tree.
  ```
- **dueDate** (optional): format `"MM/DD/YYYY HH:MM AM/PM"`. For end-of-day
  "for tomorrow" captures, set the due date to the next working day (default to
  a sensible morning time, e.g. 9:00 AM, unless the user specifies otherwise).
- **priority** (optional): `1`=high, `5`=medium, `9`=low, `0`=none. Use high
  for blocking manual steps.

## Workflow

1. Identify the follow-up(s) worth capturing per the criteria above.
2. If creating proactively (end-of-day or a detected manual step), briefly tell
   the user what you're about to add and to which list before doing it, unless
   they've already asked you to just capture it.
3. Call `apple-reminders_create_reminder` once per distinct task. Batch multiple
   tool calls in a single turn when adding several at once.
4. Confirm back to the user with the titles and list(s) used.

## Managing existing reminders

- To review what's already queued, use `apple-reminders_get_reminders`
  (optionally filter by `listName` or `completed`) or
  `apple-reminders_search_reminders`.
- When a captured manual step gets done during a session, offer to mark it
  complete via `apple-reminders_update_reminder` with `completed: true`, or
  remove it with `apple-reminders_delete_reminder`.

## Finding reminders for a project

When the user asks what's outstanding for a particular project/repo (e.g.
"what reminders do I have for apple-reminders-mcp?"), search by the project tag:

- Call `apple-reminders_search_reminders` with `searchTerm` set to
  `project:<name>` (e.g. `project:apple-reminders-mcp`). The tag lives in the
  reminder body, and search matches body text.
- If the user names a project by an informal name, map it to the same
  normalized `<name>` used when creating (repo/dir name, lowercased, hyphenated)
  before searching.
- Present the matches grouped for that project, and offer to complete or delete
  any that are already done.

## Examples

- User: "Remind me to review the migration script tomorrow."
  → create_reminder(name="Review migration script", listName="Work",
  dueDate="<next working day> 09:00 AM").

- End of day, a PR is open awaiting the user's merge in the `web-api` repo.
  → "I'll add a reminder to merge PR #123 tomorrow." → create_reminder(
  name="Merge PR #123", listName="Work",
  body="[project:web-api]\n<repo/PR link>",
  dueDate="<next working day> 09:00 AM", priority=1).

- A task needs the user to rotate a credential the agent must not touch, in the
  `billing-service` repo.
  → create_reminder(name="Rotate STRIPE_API_KEY", listName="Work",
  body="[project:billing-service]\nOld key still active; rotate in dashboard and update env.",
  priority=1).

- User: "What reminders do I have for billing-service?"
  → search_reminders(searchTerm="project:billing-service") → present matches.
