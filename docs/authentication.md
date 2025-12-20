# Authentication Setup

LocalMind supports optional authentication using [Clerk](https://clerk.com/). Authentication is **disabled by default**, making it easy to run the app locally without any setup.

## Quick Reference

| Use Case | `auth.enabled` | `auth.allow_signup` | Clerk Key Required |
|----------|----------------|---------------------|-------------------|
| Local/Desktop (no auth) | `false` | N/A | No |
| Private server (sign-in only) | `true` | `false` | Yes |
| Public deployment (sign-in + sign-up) | `true` | `true` | Yes |

## Configuration Options

Authentication is configured in `app.config.json`:

```json
{
  "auth": {
    "enabled": false,
    "allow_signup": false
  }
}
```

### Options

- **`enabled`**: Enable or disable authentication entirely
  - `false` (default): No authentication, app is accessible to anyone
  - `true`: Requires Clerk authentication to access the app

- **`allow_signup`**: Control whether new users can register
  - `false`: Only existing users can sign in (invite-only)
  - `true`: Anyone can create an account

## Setup Scenarios

### Scenario 1: No Authentication (Default)

For local development or desktop app usage where authentication is not needed.

**Configuration:**
```json
{
  "auth": {
    "enabled": false,
    "allow_signup": false
  }
}
```

No additional setup required. The app works immediately.

### Scenario 2: Sign-in Only (Private Server)

For personal deployments where only you (or invited users) should have access.

**Step 1: Create a Clerk Application**

1. Go to [Clerk Dashboard](https://dashboard.clerk.com/)
2. Create a new application
3. Navigate to **API Keys** page
4. Copy your **Publishable Key**

**Step 2: Configure Environment**

Create `.env.local` in the project root:

```bash
VITE_CLERK_PUBLISHABLE_KEY=pk_test_your_key_here
```

**Step 3: Update Configuration**

In `app.config.json`:

```json
{
  "auth": {
    "enabled": true,
    "allow_signup": false
  }
}
```

**Step 4: Add Users in Clerk Dashboard**

Since sign-up is disabled, you need to manually add users:

1. Go to Clerk Dashboard > **Users**
2. Click **Create user**
3. Enter email and password
4. The user can now sign in to your app

### Scenario 3: Public Registration (Open Access)

For deployments where anyone can create an account.

**Step 1: Create a Clerk Application**

Same as Scenario 2.

**Step 2: Configure Environment**

Create `.env.local`:

```bash
VITE_CLERK_PUBLISHABLE_KEY=pk_test_your_key_here
```

**Step 3: Update Configuration**

In `app.config.json`:

```json
{
  "auth": {
    "enabled": true,
    "allow_signup": true
  }
}
```

Users will see both "Sign in" and "Sign up" options.

## Docker/Kamal Deployment

When deploying with Docker or Kamal, pass the environment variable:

### Docker Compose

Add to `docker-compose.yml`:

```yaml
services:
  frontend:
    environment:
      - VITE_CLERK_PUBLISHABLE_KEY=${VITE_CLERK_PUBLISHABLE_KEY}
```

Then set in `.env`:

```bash
VITE_CLERK_PUBLISHABLE_KEY=pk_live_your_production_key
```

### Kamal

Add to `.kamal/secrets`:

```bash
VITE_CLERK_PUBLISHABLE_KEY=pk_live_your_production_key
```

Update `config/deploy.yml` to include the secret:

```yaml
env:
  secret:
    - VITE_CLERK_PUBLISHABLE_KEY
```

## Troubleshooting

### "Authentication Configuration Error" Message

This appears when `auth.enabled` is `true` but `VITE_CLERK_PUBLISHABLE_KEY` is not set.

**Solution:** Either:
- Set the environment variable in `.env.local`
- Or disable auth by setting `auth.enabled` to `false`

### Sign-up Button Not Appearing

If `allow_signup` is `false`, the sign-up option is hidden. This is intentional for private deployments.

**Solution:** Set `auth.allow_signup` to `true` if you want public registration.

### User Cannot Sign In

1. Verify the user exists in Clerk Dashboard
2. Check that `VITE_CLERK_PUBLISHABLE_KEY` matches your Clerk application
3. Ensure you're using the correct environment (test vs. production keys)

## Security Notes

1. **Never commit `.env.local`** - It's already in `.gitignore`
2. **Use production keys for production** - Clerk provides separate test and live keys
3. **Clerk handles security** - Passwords are never stored in LocalMind; Clerk manages all authentication securely

## Architecture

The authentication flow is handled by `ClerkProviderWrapper`:

```
ClerkProviderWrapper
├── auth.enabled = false → Render app directly (no auth)
├── auth.enabled = true, no key → Show configuration error
└── auth.enabled = true, has key → ClerkProvider
    ├── SignedIn → Render app
    └── SignedOut → Show sign-in form
```

The `UserButton` component appears in the header when a user is signed in, providing:
- User profile management
- Sign out functionality
- Account settings (via Clerk's hosted UI)
