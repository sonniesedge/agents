/**
 * Warns before a command runs in a directory you have marked as protected.
 *
 * An example. Copy it up one level into plugins/ to activate it — files in
 * examples/ are deliberately not linked out, so nothing here runs.
 *
 * Demonstrates the three things most plugins need: reading config on startup,
 * inspecting a tool call before it executes, and refusing a permission
 * request outright.
 */

import type { Plugin } from "@opencode-ai/plugin"

/** Directories where writes should never happen without a second look. */
const PROTECTED = ["/etc", "/usr", "/System"]

export const ProtectedPaths: Plugin = async ({ directory }) => {
  return {
    /**
     * Runs before every tool call. Mutating `output.args` changes what the
     * tool receives; throwing cancels the call.
     */
    "tool.execute.before": async (input, output) => {
      if (input.tool !== "bash") return

      const command = String(output.args.command ?? "")
      const hit = PROTECTED.find((dir) => command.includes(dir))
      if (hit) {
        throw new Error(
          `Refusing to run a command touching ${hit}. ` +
            `Edit plugins/protected-paths.ts if this is intentional.`,
        )
      }
    },

    /**
     * Runs whenever opencode would ask you to approve something. Setting
     * `output.status` decides it without prompting.
     *
     * Note this is a *convenience*, not a security boundary: it only sees
     * requests that reach opencode. Use permissions in opencode.jsonc, or a
     * real sandbox, for anything you actually need enforced.
     */
    "permission.ask": async (permission, output) => {
      if (
        permission.type === "bash" &&
        String(permission.title).includes("rm -rf /")
      ) {
        output.status = "deny"
      }
    },

    /** Fires for every session event. Keep it cheap — it runs a lot. */
    event: async ({ event }) => {
      if (event.type === "session.start") {
        console.log(
          `[protected-paths] watching ${PROTECTED.length} paths in ${directory}`,
        )
      }
    },
  }
}
