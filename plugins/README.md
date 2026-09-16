# plugins/

opencode plugins: JavaScript or TypeScript files that hook into opencode's
runtime to add tools, intercept events, or change behaviour.

Linked by the `plugins` target:

```yaml
targets:
  opencode:
    plugins: ~/.config/opencode/plugin
```

Every file here is linked as-is, whatever its extension, so plugins may bring
supporting files alongside them. `README.md` is skipped.

This directory is currently empty. `nono-sandbox.ts` is deliberately *not*
kept here — it is installed and updated by nono itself, into a separate
directory, and duplicating it would register the plugin twice.

## Not a skill

A plugin is executable code that changes what opencode can do. A skill is
instructions that change what the agent knows. Reach for a skill first;
plugins are for behaviour that instructions cannot express.

See [the plugins docs](https://opencode.ai/docs/plugins/).
