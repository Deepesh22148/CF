'use client'

import React, { KeyboardEvent, useMemo, useState } from "react"

interface GenreChipInputProps {
  label: string
  placeholder: string
  selectedGenres: string[]
  availableGenres: string[]
  onChange: (next: string[]) => void
}

const normalizeGenre = (value: string) =>
  value.trim().toLowerCase().replace(/\s+/g, "_").replace(/-/g, "_")

const GenreChipInput = ({
  label,
  placeholder,
  selectedGenres,
  availableGenres,
  onChange,
}: GenreChipInputProps) => {
  const [query, setQuery] = useState<string>("")
  const [showSuggestions, setShowSuggestions] = useState<boolean>(false)

  const selectedSet = useMemo(() => new Set(selectedGenres.map((g) => normalizeGenre(g))), [selectedGenres])

  const suggestions = useMemo(() => {
    const q = normalizeGenre(query)
    if (!q) {
      return availableGenres.filter((g) => !selectedSet.has(normalizeGenre(g))).slice(0, 10)
    }

    const prefix = availableGenres.filter(
      (g) => normalizeGenre(g).startsWith(q) && !selectedSet.has(normalizeGenre(g)),
    )
    const contains = availableGenres.filter(
      (g) => normalizeGenre(g).includes(q) && !normalizeGenre(g).startsWith(q) && !selectedSet.has(normalizeGenre(g)),
    )
    return [...prefix, ...contains].slice(0, 10)
  }, [availableGenres, query, selectedSet])

  const addGenre = (genre: string) => {
    const normalized = normalizeGenre(genre)
    if (selectedSet.has(normalized)) {
      setQuery("")
      setShowSuggestions(false)
      return
    }

    onChange([...selectedGenres, normalized])
    setQuery("")
    setShowSuggestions(false)
  }

  const removeGenre = (genre: string) => {
    onChange(selectedGenres.filter((g) => normalizeGenre(g) !== normalizeGenre(genre)))
  }

  const onKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key !== "Enter") {
      return
    }
    e.preventDefault()

    const normalized = normalizeGenre(query)
    if (!normalized) {
      return
    }

    const exact = availableGenres.find((g) => normalizeGenre(g) === normalized)
    if (exact) {
      addGenre(exact)
      return
    }

    if (suggestions.length > 0) {
      addGenre(suggestions[0])
    }
  }

  return (
    <div>
      <label className="block text-sm mb-2">{label}</label>

      <div className="relative">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setShowSuggestions(true)}
          onBlur={() => setTimeout(() => setShowSuggestions(false), 120)}
          onKeyDown={onKeyDown}
          placeholder={placeholder}
          className="w-full rounded-lg bg-slate-800 px-3 py-2"
        />

        {showSuggestions && suggestions.length > 0 && (
          <div className="absolute z-20 mt-1 w-full rounded-lg border border-white/10 bg-slate-900 shadow-lg max-h-56 overflow-y-auto">
            {suggestions.map((genre) => (
              <button
                type="button"
                key={genre}
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => addGenre(genre)}
                className="w-full px-3 py-2 text-left text-sm hover:bg-slate-800"
              >
                {genre}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="mt-2 flex flex-wrap gap-2">
        {selectedGenres.map((genre) => (
          <span
            key={genre}
            className="inline-flex items-center gap-2 rounded-full bg-emerald-500/20 text-emerald-200 px-3 py-1 text-sm"
          >
            {genre}
            <button
              type="button"
              onClick={() => removeGenre(genre)}
              className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-emerald-400/20 hover:bg-emerald-400/40"
              aria-label={`Remove ${genre}`}
            >
              x
            </button>
          </span>
        ))}
      </div>
    </div>
  )
}

export default GenreChipInput
