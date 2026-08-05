import { Coffee } from "lucide-react";

export default function Home() {
  return (
    <main className="flex flex-1 items-center justify-center px-6 py-24">
      <div className="flex max-w-xl flex-col items-center gap-4 text-center">
        <Coffee className="size-10 text-primary" />
        <h1 className="text-4xl font-semibold tracking-tight text-foreground">
          MoodBrew
        </h1>
        <p className="text-lg text-muted-foreground">
          Recomendador de cafeterías de especialidad. Cuéntame dónde estás y qué te
          apetece.
        </p>
      </div>
    </main>
  );
}
