# Bitwarden Environment Variables

Securely use and share environment variables in your local development using [Bitwarden](https://bitwarden.com/)!

## Before Using This Tool

Before using this tool, it is recommended you take a look at [Bitwarden Secrets Manager](https://bitwarden.com/products/secrets-manager/) and see if it fulls your needs. At the time of writing, it is in beta and does not have the ability to replicate this tool's feature set. However, the Bitwarden Secrets Manager CLI is described as ["a powerful tool for retrieving and injecting your secrets"](https://bitwarden.com/help/secrets-manager-cli/), so it may be possible to replicate this tool with their native offering in the future.

## Why Use This Tool

In short, storing your secrets (e.g., API keys, client secrets, etc.) in a plaintext `.env` file is insecure and not portable. If your computer is ever hacked or stolen, the perpetrator will have easy access to this data. Additionally, with any distributed system without a central source of truth, it can be hard to know what the most up-to-date version of any secret is. In other words, when working in a team, storing your secrets in a secrets/passwords manager makes it is much easier to keep everyone in sync. This tool helps bridge the gap between storing these secrets in Bitwarden, and using these secrets in your shell.

## Install

...

<!-- This tool requires the [Bitwarden CLI](https://bitwarden.com/help/cli/). Make sure it is on your `PATH` before using this tool. -->
<!-- This will not create environment variables for key-values defined without the `bwenv://` prefix. -->

## Is it safe to commit the generated `.env`?

You should still avoid committing your `.env`, however if your `.env` is exposed, none of the information in the generated secret reference string is sensitive. You would still need the Bitwarden credentials to make use of this information.

## What about 1Password?

1Password already has native support this for feature, and it is called [Secret References](https://developer.1password.com/docs/cli/secret-references).
