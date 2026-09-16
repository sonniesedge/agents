---
name: chezmoi
description: |-
  Manage dotfiles with chezmoi — a declarative, version-controlled dotfile manager. Use for
  initializing chezmoi on new machines, adding/editing/removing managed files, creating templates
  for machine-specific configs, managing file permissions/symlinks/encryption, and syncing across
  machines. Use proactively when the user mentions dotfiles, .bashrc, .zshrc, gitconfig, editor
  configs, SSH keys, or wants their config synced across machines.

  Examples:
  - user: "Set up chezmoi" → run chezmoi init, create source directory structure
  - user: "Add my .zshrc to chezmoi" → chezmoi add ~/.zshrc, explain source naming
  - user: "Make .vimrc different on Linux vs macOS" → create template with if/eq logic
  - user: "Sync my dotfiles to a new machine" → chezmoi init --apply <repo>
  - user: "Ensure .ssh/config is mode 600" → use private_ prefix attribute
---

# Chezmoi

Declarative dotfile manager. Stores desired state in `~/.local/share/chezmoi` (source directory).
When you run `chezmoi apply`, it computes the target state and makes minimal changes to match.

## Core Concepts

| Concept | Description |
|---------|-------------|
| **Source directory** | `~/.local/share/chezmoi` by default — stores desired state |
| **Target** | A file, directory, or symlink in the destination (usually `~`) |
| **Config file** | `~/.config/chezmoi/chezmoi.toml` — machine-specific settings |
| **Template** | File with `.tmpl` suffix or in `.chezmoitemplates/` — uses Go templating |

## Naming Convention (Source → Target)

File names in the source directory encode target behavior via prefixes/suffixes:

### Prefixes (in order)

| Prefix | Effect | Example |
|--------|--------|---------|
| `dot_` | Leading dot in target | `dot_bashrc` → `.bashrc` |
| `private_` | Mode 0600 (owner read/write only) | `private_ssh_config` → `.ssh/config` mode 600 |
| `readonly_` | Remove write permissions | `readonly_gitconfig` → `.gitconfig` read-only |
| `executable_` | Add executable permission | `executable_zshrc` → `.zshrc` with +x |
| `create_` | Create if missing, but don't overwrite | `create_kube_config` → `.kube/config` (only if absent) |
| `symlink_` | Create as symlink | `symlink_src` → `src` (symlink) |
| `empty_` | Ensure file exists even if empty | `empty_gitattributes` → `.gitattributes` (keep empty) |
| `encrypted_` | Encrypt with age/gpg | `encrypted_github_token.age` → decrypted at apply time |
| `run_` / `before_` / `after_` | Scripts to run | `run_install_plugins.sh` → runs on apply |
| `modify_` | Script that modifies existing file via stdin/stdout | `modify_bashrc` → receives current contents, writes new |
| `remove_` | Remove target if it exists | `remove_old_config` → deletes `.oldconfig` |
| `exact_` | Remove anything not managed by chezmoi in target dir | `exact_src` → removes unmanaged files in `src/` |

### Suffixes

| Suffix | Effect |
|--------|---------|
| `.tmpl` | Contents are Go templates (uses `{{ }}` syntax) |
| `.age` | Encrypted with age (stripped from target name) |
| `.asc` | Encrypted with GPG (stripped from target name) |
| `.literal` | Stop parsing attributes |

### Target Types (directory naming)

To manage a directory, create it in source:
```bash
mkdir -p $(chezmoi source-path)/src          # creates ~/src
touch $(chezmoi source-path)/src/.keep       # git won't ignore it
```

## Daily Workflow

### Adding a file
```bash
chezmoi add ~/.bashrc              # copies to source as dot_bashrc
chezmoi add --template ~/.zshrc    # adds with .tmpl suffix for templating
```

### Editing a file
```bash
chezmoi edit ~/.bashrc             # opens source file in $EDITOR, validates template on save
chezmoi edit --apply ~/.bashrc     # same but also applies changes after saving
```

### Reviewing and applying
```bash
chezmoi diff                       # shows what chezmoi apply would change
chezmoi status                     # summary of changes
chezmoi apply -v                   # apply with verbose output (dry-run: -n -v)
```

### Committing changes
```bash
chezmoi cd                         # opens subshell in source directory
git add . && git commit -m "message"
exit                               # returns to previous working directory
```

### Updating from remote
```bash
chezmoi update -v                  # pull latest and apply
```

## Templates (Machine-Specific Configs)

Templates use Go `text/template` syntax with [sprig](http://masterminds.github.io/sprig/) functions.

### Available template data
```bash
chezmoi data                       # print all available variables as JSON
```

Key built-in variables:
- `.chezmoi.os` — OS (e.g., "darwin", "linux")
- `.chezmoi.arch` — Architecture
- `.chezmoi.hostname` — Machine hostname
- `.chezmoi.username` — Username
- `.chezmoi.homeDir` — Home directory path
- `.chezmoi.path` — chezmoi executable path
- `.chezmoi.sourceDir` — Source directory path
- `.chezmoi.env` — Environment variables (map)

### Creating templates
```bash
# Method 1: Add with --template flag
chezmoi add --template ~/.zshrc

# Method 2: Rename existing file to .tmpl
mv $(chezmoi source-path)/dot_zshrc $(chezmoi source-path)/dot_zshrc.tmpl

# Method 3: Create manually
chezmoi cd && $EDITOR dot_zshrc.tmpl
```

### Template examples

Conditional logic:
```
# ~/.local/share/chezmoi/dot_bashrc.tmpl
export EDITOR=vim

{{- if eq .chezmoi.os "darwin" }}
# macOS-specific config
export PATH="/opt/homebrew/bin:$PATH"
{{- end }}

{{- if eq .chezmoi.hostname "work-laptop" }}
# Work-specific config
export WORK_ENV=1
{{- end }}
```

Using environment variables:
```
# ~/.local/share/chezmoi/dot_gitconfig.tmpl
[user]
    name = {{ .chezmoi.env.GIT_NAME | default "My Name" }}
    email = {{ .chezmoi.env.GIT_EMAIL | default "me@example.com" }}
```

Including reusable templates:
```bash
# Create shared template
chezmoi cd && mkdir -p .chezmoitemplates && $EDITOR base-config

# Use in another file
# ~/.local/share/chezmoi/dot_file.tmpl
{{- template "base-config" . }}
additional: config
```

### Testing templates
```bash
chezmoi execute-template '{{ .chezmoi.hostname }}'    # test a fragment
chezmoi cat ~/.zshrc                                   # render template without applying
chezmoi cd && chezmoi execute-template < dot_zshrc.tmpl # test full file
```

## Special Files and Directories

| File/Dir | Purpose |
|----------|---------|
| `.chezmoiignore` | Glob patterns of files to ignore (like .gitignore) |
| `.chezmoiremove` | Patterns of targets to remove on apply |
| `.chezmoiscripts/` | Scripts that run during apply (run_, before_, after_ scripts) |
| `.chezmoitemplates/` | Reusable template fragments (included via `{{ template "name" }}`) |
| `.chezmoidata.json/yaml/toml` | Custom data available as template variables via `.data` |

### .chezmoiignore
```bash
# ~/.local/share/chezmoi/.chezmoiignore
node_modules/
__pycache__/
*.swp
```

### .chezmoiremove
```bash
# ~/.local/share/chezmoi/.chezmoiremove
old-config.bak
deprecated-tool/
```

## Encryption (age — recommended)

```bash
# Generate age key
chezmoi age-keygen

# Encrypt a file (adds .age suffix)
echo "my-secret-token" | chezmoi encrypt > $(chezmoi source-path)/private_github_token.age

# Or add existing file
chezmoi add --encrypt ~/.netrc          # uses age by default

# Edit encrypted file (auto-decrypts for editing)
chezmoi edit-encrypted ~/.netrc
```

## Password Manager Integration

chezmoi supports many password managers via template functions:

```bash
# Check available data for your PM
chezmoi data
```

Common template functions:
- `bitwarden` / `1password` / `lastpass` / `keepassxc` — retrieve secrets
- `secret` / `secretJSON` — chezmoi's built-in secret storage

```
# Example: retrieve from 1Password
{{ with onepassword "login" "my-credential" }}
password: {{ .password }}
{{ end }}

# Example: chezmoi built-in secret
{{ secret "github-token" }}
```

## Configuration File

Default location: `~/.config/chezmoi/chezmoi.toml` (supports json, yaml, toml)

```toml
# ~/.config/chezmoi/chezmoi.toml
sourceDir = "/path/to/dotfiles"    # custom source directory

[git]
    autoPush = true                 # auto-commit and push changes

[encrypt]
    command = "age"                 # encryption tool (default: age)

[terminal]
    editor = "code --wait"          # default editor for chezmoi edit

[system.chmod]
    createMode = "0600"             # default file permissions for new files
```

## Key Commands Reference

| Command | Purpose |
|---------|---------|
| `chezmoi doctor` | Diagnose common problems — run this first if something is unexpected |
| `chezmoi init [repo]` | Initialize source directory, optionally from a remote repo |
| `chezmoi init --apply [repo]` | Init and immediately apply on a new machine |
| `chezmoi add <path>` | Add file to source directory |
| `chezmoi edit <file>` | Edit file in source directory via $EDITOR |
| `chezmoi diff` | Preview changes chezmoi apply would make |
| `chezmoi status` | Summary of managed files and pending changes |
| `chezmoi apply [-v]` | Apply source state to destination directory |
| `chezmoi update [-v]` | Pull from remote and apply |
| `chezmoi cd` | Open subshell in source directory |
| `chezmoi data` | Print all template variables as JSON |
| `chezmoi managed` | List files chezmoi manages in destination |
| `chezmoi unmanaged` | List files NOT managed by chezmoi |
| `chezmoi remove <file>` | Remove file from source directory (keeps target) |
| `chezmoi rm <file>` | Remove file from source directory AND delete target |
| `chezmoi import <url>` | Import files from a URL/archive |
| `chezmoi archive` | Create an archive of the source state |
| `chezmoi chattr <flags> <file>` | Change attributes (e.g., `+template`, `-private`) |
| `chezmoi merge <file>` | Merge changes using $MERGE tool (default: vimdiff) |
| `chezmoi verify` | Verify encrypted files can be decrypted |

## Migration from Existing Dotfiles

To migrate existing dotfiles to chezmoi:
```bash
# Initialize chezmoi
chezmoi init

# Add existing files one by one
for f in ~/.bashrc ~/.zshrc ~/.gitconfig ~/.vimrc; do
    chezmoi add "$f"
done

# Review and commit
chezmoi diff
chezmoi cd && git add . && git commit -m "Initial dotfiles" && exit

# Push to remote
git remote add origin git@github.com:USERNAME/dotfiles.git
git branch -M main && git push -u origin main
```

## Common Patterns

### Machine-specific configs
Use `.chezmoi.hostname` or `.chezmoi.os` in templates to branch logic.

### Symlinking files managed elsewhere
```bash
# Create symlink from source to target
echo '{{ .chezmoi.sourceDir }}/myapp.conf' > $(chezmoi source-path)/symlink_myapp_conf
```

### Ensuring file permissions without changing contents
Create an empty file with `private_` prefix:
```bash
touch $(chezmoi source-path)/dot_kube/private_config    # ensures ~/.kube/config is mode 600
```

### Managing files modified by applications
Use `.chezmoiignore` to ignore the file, then symlink back to source:
```bash
echo 'settings.json' >> $(chezmoi source-path)/.chezmoiignore
mkdir -p $(chezmoi source-path)/private_dot_config/private_Code/User
echo '{{ .chezmoi.sourceDir }}/settings.json' > $(chezmoi source-path)/private_dot_config/private_Code/User/symlink_settings.json.tmpl
```

### External files (downloaded from URLs)
Create `~/.local/share/chezmoi/.chezmoiexternals/gitignore_global.toml`:
```toml
[gitignore_global]
    url = "https://raw.githubusercontent.com/github/gitignore/master/Global.gitignore"
    type = "file"
```
