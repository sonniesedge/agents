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
supporting files alongside them. `README.md` and `examples/` are skipped.

## Writing one

A plugin exports a function returning hooks. The ones you will reach for
first:

| hook | when it runs |
| --- | --- |
| `tool.execute.before` | before any tool call — mutate its args, or throw to cancel |
| `tool.execute.after` | after a tool call — rewrite its output |
| `permission.ask` | when opencode would prompt you — answer it automatically |
| `event` | every session event |
| `tool` | register entirely new tools |

See `examples/protected-paths.ts` for a worked example using the first three.
Copy it up one level to activate it: `examples/` is deliberately not linked
out, so nothing in there is ever loaded.

Plugins run as real code with no sandbox. A `permission.ask` hook is a
convenience, not a security boundary — it only sees requests that reach
opencode. Use `permission` in `opencode.jsonc`, or an actual sandbox, for
anything that must be enforced.

## Nothing here yet

`nono-sandbox.ts` is deliberately *not* kept here — it is installed and
updated by nono itself, into a separate directory, and duplicating it would
register the plugin twice.

## Not a skill

A plugin is executable code that changes what opencode can do. A skill is
instructions that change what the agent knows. Reach for a skill first;
plugins are for behaviour that instructions cannot express.

See [the plugins docs](https://opencode.ai/docs/plugins/).
