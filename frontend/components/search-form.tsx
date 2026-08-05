"use client";

import { Coffee } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

const EXAMPLES = [
  "Café tranquilo con wifi en Ixelles, Bruselas",
  "Un espresso de especialidad cerca de la Giralda, Sevilla",
  "Un flat white abierto ahora en el Born, Barcelona",
];

type Props = {
  value: string;
  onChange: (value: string) => void;
  onSearch: (text: string) => void;
  loading: boolean;
};

export function SearchForm({ value, onChange, onSearch, loading }: Props) {
  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap gap-2">
        {EXAMPLES.map((example) => (
          <Button
            key={example}
            type="button"
            variant="outline"
            size="sm"
            disabled={loading}
            className="h-auto max-w-full py-1.5 text-left whitespace-normal"
            onClick={() => {
              onChange(example);
              onSearch(example);
            }}
          >
            {example}
          </Button>
        ))}
      </div>

      <form
        className="flex flex-col gap-2 sm:flex-row"
        onSubmit={(event) => {
          event.preventDefault();
          onSearch(value);
        }}
      >
        <Input
          value={value}
          onChange={(event) => onChange(event.target.value)}
          disabled={loading}
          placeholder="Ciudad + un punto exacto. Ej.: café con wifi cerca de la Giralda, Sevilla"
          className="h-10 flex-1"
        />
        <Button type="submit" size="lg" disabled={loading} className="h-10">
          <Coffee /> Recomiéndame
        </Button>
      </form>

      <p className="text-xs text-muted-foreground">
        Para acertar necesito la ciudad y un punto concreto: barrio, monumento, plaza o
        calle. Evita nombres sueltos («Centro», «Gràcia»).
      </p>
    </div>
  );
}
