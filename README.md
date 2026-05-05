# envault

> Manage and sync encrypted `.env` files across team members using a shared backend store.

---

## Installation

```bash
pip install envault
```

Or with [pipx](https://pypa.github.io/pipx/):

```bash
pipx install envault
```

---

## Usage

**Push your local `.env` to the shared store:**

```bash
envault push --env .env --project myapp
```

**Pull the latest `.env` for a project:**

```bash
envault pull --project myapp --output .env
```

**Initialize a new project vault:**

```bash
envault init --project myapp --backend s3://my-bucket/envault
```

Team members authenticate once and always stay in sync with the latest secrets — no more manually sharing `.env` files over Slack or email.

---

## How It Works

1. Your `.env` file is encrypted locally using a shared project key before upload.
2. Encrypted secrets are stored in a configured backend (S3, GCS, or a self-hosted store).
3. Team members with access can pull and decrypt the file instantly.

---

## Configuration

Set your backend and credentials in `~/.envault/config.toml`:

```toml
[defaults]
backend = "s3://my-bucket/envault"
region  = "us-east-1"
```

---

## License

This project is licensed under the [MIT License](LICENSE).