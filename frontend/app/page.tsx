import { Coffee } from "lucide-react";
import { SearchExperience } from "@/components/search-experience";

export default function Home() {
  return (
    <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-8 px-6 py-12 sm:py-16">
      <header className="flex flex-col gap-2">
        <div className="flex items-center gap-2">
          <Coffee className="size-7 text-primary" />
          <h1 className="text-3xl font-semibold tracking-tight text-foreground">
            MoodBrew
          </h1>
        </div>
        <p className="text-muted-foreground">
          Recomendador de cafeterías de especialidad. Cuéntame dónde estás y qué te
          apetece.
        </p>
      </header>

      <SearchExperience />

      <footer className="mt-auto pt-8 text-xs text-muted-foreground">
        Datos de OpenStreetMap vía Geoapify · MoodBrew
      </footer>
    </main>
  );
}
