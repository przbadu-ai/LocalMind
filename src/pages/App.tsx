import { Button } from "@/components/ui/button";

function App() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <div className="text-center space-y-6">
        <h1 className="text-4xl font-bold text-gray-900 dark:text-white">
          Welcome to Local Mind
        </h1>
        <p className="text-lg text-gray-600 dark:text-gray-300">
          Tailwind CSS + shadcn/ui is configured!
        </p>
        <div className="flex gap-4 justify-center">
          <Button>Default Button</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="destructive">Destructive</Button>
          <Button variant="outline">Outline</Button>
        </div>
      </div>
    </main>
  );
}

export default App;
