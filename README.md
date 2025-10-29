# Tiberius

<a alt="Nx logo" href="https://nx.dev" target="_blank" rel="noreferrer"><img src="https://raw.githubusercontent.com/nrwl/nx/master/images/nx-logo.png" width="45"></a>

Welcome to Tiberius, the mono repo for  management.

# Getting Started
## Prerequisites
Install NVM (node version manager) if not installed.
```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
```

Get the code base
```bash
git clone git@github.com:Nimrox-ai/tiberius.git
cd tiberius  # Very important - we assume are in this folder from now on
```

**==> 🚀🚀🚀 All the rest of the instructions assume you are in the tiberius folder. <==**

Install needed VSCode extensions:
```bash
cd .vscode && cat extensions.json | jq -r '.recommendations[]' | xargs -n 1 code --install-extension && cd ..
```

Set git config:
```bash
git config --global pull.rebase true
git config user.name "Your Name"
git config user.email "your.name@nimrox.ai"
```

Install Python:
```bash
brew install pyenv
brew install pyenv-virtualenv
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
pyenv install 3.12.3
```

Install Maven:
```bash
brew install maven
```

Install Java:
Download and install the [Java ARM DMG](https://www.oracle.com/java/technologies/downloads/#java21:~:text=https%3A//download.oracle.com/java/21/latest/jdk%2D21_macos%2Daarch64_bin.dmg).

Install node modules:
```bash
npm install
npm run prepare  # Initializes husky hooks
```

## Clean Up Folders
Java is finikity (to say the least). Do the following to ensure that VSCode can correctly work with Java:

```bash
rm -rf .project .classpath .settings
rm -rf apps/falcon-iq-rest/.project apps/falcon-iq-rest/.classpath apps/falcon-iq-rest/.settings
rm -rf ~/Library/Application\ Support/Code/User/workspaceStorage/*/redhat.java
```

# 🚀 Congratulations, you are now ready to develop!

# Working With This Repo
This is a mono repo. As such, there are multiple apps and tools all sharing this code base. The following holds true for everything within this repo.

### Environments
There are three environments:
 1. *development*
 2. *staging*
 3. *production*

The above environments will never be shortened in code (e.g. *development* will <u>never</u> be *dev*).

### Project Commands
Every project is defined by a `project.json` file, which (among other things) defines its *name*. Each project also defines targets (commands). The following targets are common across all projects:

 * **build** builds a project. There are <u>three</u> flavors of build:
   * **build:dev** build a development environment.
   * **build:staging** build a staging environment.
   * **build:production** build a production environment.
 * **dev** will run the local development environment of a project. There could also be variants of this, like:
 * **deploy** deploys a project. There are <u>two</u> flavors of deploy:
   * **deploy:staging** deploys the staging environment.
   * **deploy:production** deploys the production environment.
 * **test** launches unit/integration tests.

The above commands are constant in all projects, however there can be variants of the above, for example:
* **dev:wrangler** or **build:wrangler** or **build:standalone**