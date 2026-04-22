'use client'

import React, { KeyboardEvent, useEffect, useMemo, useState } from "react"

interface SuggestionsResponse {
  suggestions?: string[]
}

interface MovieAutocompleteChipsProps {
  label: string
  placeholder: string
  selectedMovies: string[]
  onChange: (next: string[]) => void
  maxItems?: number
}

const MovieAutocompleteChips = ({
  label,
  placeholder,
  selectedMovies,
  onChange,
  maxItems = 12,
}: MovieAutocompleteChipsProps) => {
  const [query, setQuery] = useState<string>("")
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [loading, setLoading] = useState<boolean>(false)
  const [showSuggestions, setShowSuggestions] = useState<boolean>(false)

  const selectedLowerSet = useMemo(
    () => new Set(selectedMovies.map((m) => m.toLowerCase())),
    [selectedMovies],
  )

  useEffect(() => {
    const trimmed = query.trim()
    if (!trimmed) {
      setSuggestions([])
      setShowSuggestions(false)
      return
    }

    const timer = setTimeout(async () => {
      setLoading(true)
      try {
        const response = await fetch(
          `/api/recommend/suggestions?q=${encodeURIComponent(trimmed)}&limit=8`,
        )
        const payload = (await response.json()) as SuggestionsResponse
        if (!response.ok) {
          setSuggestions([])
          setShowSuggestions(false)
          return
        }

        const fetched = (payload.suggestions || []).filter(
          (title) => !selectedLowerSet.has(title.toLowerCase()),
        )
        setSuggestions(fetched)
        setShowSuggestions(fetched.length > 0)
      } catch {
        setSuggestions([])
        setShowSuggestions(false)
      } finally {
        setLoading(false)
      }
    }, 180)

    return () => clearTimeout(timer)
  }, [query, selectedLowerSet])

  const addMovie = (title: string) => {
    if (selectedLowerSet.has(title.toLowerCase())) {
      setQuery("")
      setSuggestions([])
      setShowSuggestions(false)
      return
    }
    if (selectedMovies.length >= maxItems) {
      return
    }

    onChange([...selectedMovies, title])
    setQuery("")
    setSuggestions([])
    setShowSuggestions(false)
  }

  const removeMovie = (title: string) => {
    onChange(selectedMovies.filter((m) => m !== title))
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key !== "Enter") {
      return
    }
    e.preventDefault()
    if (!query.trim()) {
      return
    }

    const exact = suggestions.find(
      (s) => s.toLowerCase() === query.trim().toLowerCase(),
    )
    if (exact) {
      addMovie(exact)
      return
    }

    if (suggestions.length > 0) {
      addMovie(suggestions[0])
    }
  }

  return (
    <div>
      <label className="block text-sm mb-2">{label}</label>

      <div className="relative">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setShowSuggestions(suggestions.length > 0)}
          onBlur={() => setTimeout(() => setShowSuggestions(false), 120)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="w-full rounded-lg bg-slate-800 px-3 py-2"
        />

        {showSuggestions && (
          <div className="absolute z-20 mt-1 w-full rounded-lg border border-white/10 bg-slate-900 shadow-lg max-h-56 overflow-y-auto">
            {suggestions.map((title) => (
              <button
                type="button"
                key={title}
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => addMovie(title)}
                className="w-full px-3 py-2 text-left text-sm hover:bg-slate-800"
              >
                {title}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="mt-2 flex flex-wrap gap-2">
        {selectedMovies.map((title) => (
          <span
            key={title}
            className="inline-flex items-center gap-2 rounded-full bg-blue-500/20 text-blue-200 px-3 py-1 text-sm"
          >
            {title}
            <button
              type="button"
              onClick={() => removeMovie(title)}
              className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-blue-400/20 hover:bg-blue-400/40"
              aria-label={`Remove ${title}`}
            >
              x
            </button>
          </span>
        ))}
      </div>

      <p className="mt-1 text-xs text-slate-500">
        {loading ? "Searching..." : "Pick from suggestions, then remove with x."}
      </p>
    </div>
  )
}

export default MovieAutocompleteChips
