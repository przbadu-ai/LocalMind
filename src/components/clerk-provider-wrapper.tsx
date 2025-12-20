import { ClerkProvider, SignedIn, SignedOut, SignIn } from "@clerk/clerk-react";
import { AUTH_ENABLED, SIGNUP_ALLOWED } from "@/config/app-config";

const PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;

interface ClerkProviderWrapperProps {
  children: React.ReactNode;
}

function AuthGate({ children }: { children: React.ReactNode }) {
  return (
    <>
      <SignedIn>{children}</SignedIn>
      <SignedOut>
        <div className="min-h-screen flex items-center justify-center bg-background">
          <div className="w-full max-w-md p-4">
            <SignIn
              appearance={{
                elements: {
                  rootBox: "w-full",
                  card: "shadow-lg",
                },
              }}
              signUpUrl={SIGNUP_ALLOWED ? undefined : ""}
            />
          </div>
        </div>
      </SignedOut>
    </>
  );
}

export function ClerkProviderWrapper({ children }: ClerkProviderWrapperProps) {
  // If auth is not enabled, just render children directly
  if (!AUTH_ENABLED) {
    return <>{children}</>;
  }

  // Auth is enabled but no publishable key - show error
  if (!PUBLISHABLE_KEY) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center p-8 max-w-md">
          <h1 className="text-xl font-semibold text-destructive mb-4">
            Authentication Configuration Error
          </h1>
          <p className="text-muted-foreground">
            Authentication is enabled but VITE_CLERK_PUBLISHABLE_KEY is not set.
            Please add your Clerk publishable key to .env.local file.
          </p>
        </div>
      </div>
    );
  }

  return (
    <ClerkProvider publishableKey={PUBLISHABLE_KEY} afterSignOutUrl="/">
      <AuthGate>{children}</AuthGate>
    </ClerkProvider>
  );
}
