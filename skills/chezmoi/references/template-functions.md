# chezmoi Template Functions Reference

chezmoi uses Go's `text/template` engine with [sprig](http://masterminds.github.io/sprig/) functions.

## Best Reference
For the complete list, see: https://masterminds.github.io/sprig/

## Commonly Used Functions

### String
| Function | Example | Result |
|----------|---------|--------|
| `trim` | `"  hello  " | trim` | `hello` |
| `upper` / `lower` | `"HELLO" | upper` | `hello` |
| `replace` | `"foo,bar" | replace "," ";"` | `foo;bar` |
| `title` | `"hello world" | title` | `Hello World` |
| `abbrev` | `"longstring" | abbrev 5` | `lo...` |
| `default` | `"" | default "fallback"` | `fallback` |

### Conditionals
| Function | Example | Result |
|----------|---------|--------|
| `if/else` | `{{ if eq .chezmoi.os "darwin" }}macOS{{ end }}` | conditional output |
| `ternary` | `"value" | ternary "yes" "no"` | `yes` |

### Lists
| Function | Example | Result |
|----------|---------|--------|
| `join` | `list "a" "b" | join ","` | `a,b` |
| `splitList` | `"a,b,c" | splitList ","` | `[a b c]` |
| `first` / `last` | `list 1 2 3 | first` | `1` |
| `sortAlpha` | `list "c" "a" "b" | sortAlpha` | `[a b c]` |

### File/Path
| Function | Example | Result |
|----------|---------|--------|
| `fileExists` | `fileExists "/path"` | `true/false` |
| `isDir` | `isDir "/path"` | `true/false` |

### Environment
| Function | Example | Result |
|----------|---------|--------|
| `getenv` | `getenv "HOME"` | `/Users/username` |
| `expandenv` | `"${HOME}/file"` | `/Users/username/file` |

### chezmoi-specific
| Function | Example | Result |
|----------|---------|--------|
| `get` | `.chezmoi.env | get "KEY"` | value of KEY env var |
| `secret` | `secret "github-token"` | retrieves from chezmoi secret store |

## Template Best Practices

- Use `{{-` and `-}}` to trim whitespace
- Always test templates with `chezmoi execute-template '{{ .variable }}'` before applying
- Use `.chezmoi.env` for sensitive values that should be set per-machine (not committed)
- Use `private_` prefix or `.age` extension for truly sensitive data (passwords, tokens)
