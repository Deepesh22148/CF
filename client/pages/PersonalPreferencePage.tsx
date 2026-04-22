'use client'
import React, { useMemo, useState } from "react"
import MovieAutocompleteChips from "../components/ui/movie-autocomplete-chips"
import GenreChipInput from "../components/ui/genre-chip-input"

interface Recommendation {
  movie_id: number
  title: string
  genres: string
  score: number
  estimated_rating: number
  reason: string
  summary: string
}

interface PersonalResponse {
  user_info: {
    age: number
    gender: string
    occupation: string
    genres: string[]
  }
  recommendations: Recommendation[]
  rate_limited: boolean
  system_notes?: string[]
  search_analysis?: string
  cluster?: {
    cluster_id: number
    profile?: {
      dominant_genres?: string[]
      top_movies?: { title: string }[]
    }
  }
}

const allGenres = [
  "action",
  "adventure",
  "animation",
  "children",
  "comedy",
  "crime",
  "documentary",
  "drama",
  "fantasy",
  "film_noir",
  "horror",
  "musical",
  "mystery",
  "romance",
  "sci_fi",
  "thriller",
  "war",
  "western",
]

const PersonalPreferencePage = () => {
  const [age, setAge] = useState<string>("25")
  const [gender, setGender] = useState<string>("M")
  const [occupation, setOccupation] = useState<string>("student")
  const [genresInput, setGenresInput] = useState<string[]>(["drama", "comedy"])
  const [similarMovies, setSimilarMovies] = useState<string[]>([])
  const [dislikedMovies, setDislikedMovies] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [results, setResults] = useState<PersonalResponse | null>(null)

  const suggestedGenreHint = useMemo(() => allGenres.join(", "), [])

  const getRecommendations = async () => {
    const ageValue = Number(age)
    if (Number.isNaN(ageValue) || ageValue < 1 || ageValue > 120) {
      setError("Please enter a valid age")
      return
    }

    setError(null)
    setLoading(true)
    setResults(null)

    try {
      const res = await fetch("/api/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mode: "personal",
          age: ageValue,
          gender,
          occupation,
          genres: genresInput,
          similar_movies: similarMovies,
          disliked_movies: dislikedMovies,
          top_k: 15,
        }),
      })

      const data = await res.json()
      if (!res.ok) {
        setError(data?.error || data?.detail || "Unable to fetch recommendations")
        return
      }

      setResults(data)
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Unknown error"
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 py-12 px-6">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-3xl font-bold mb-2">Fresh User Recommendations</h1>
        <p className="text-slate-400 mb-8">
          Enter profile details and the model will map you to a behavior cluster, then rank movies with explainable reasoning.
        </p>

        <div className="grid md:grid-cols-2 gap-4 bg-slate-900 border border-white/10 p-6 rounded-xl">
          <div>
            <label className="block text-sm mb-2">Age</label>
            <input
              value={age}
              onChange={(e) => setAge(e.target.value)}
              type="number"
              className="w-full rounded-lg bg-slate-800 px-3 py-2"
            />
          </div>

          <div>
            <label className="block text-sm mb-2">Gender</label>
            <select
              value={gender}
              onChange={(e) => setGender(e.target.value)}
              className="w-full rounded-lg bg-slate-800 px-3 py-2"
            >
              <option value="M">Male</option>
              <option value="F">Female</option>
              <option value="O">Other</option>
            </select>
          </div>

          <div>
            <label className="block text-sm mb-2">Occupation</label>
            <input
              value={occupation}
              onChange={(e) => setOccupation(e.target.value)}
              placeholder="engineer"
              className="w-full rounded-lg bg-slate-800 px-3 py-2"
            />
          </div>

          <GenreChipInput
            label="Preferred Genres"
            placeholder="Search and add genres"
            selectedGenres={genresInput}
            availableGenres={allGenres}
            onChange={setGenresInput}
          />

          <MovieAutocompleteChips
            label="Liked Movies (optional)"
            placeholder="Search and add liked movies"
            selectedMovies={similarMovies}
            onChange={setSimilarMovies}
          />

          <MovieAutocompleteChips
            label="Disliked Movies (optional)"
            placeholder="Search and add disliked movies"
            selectedMovies={dislikedMovies}
            onChange={setDislikedMovies}
          />
        </div>

        <p className="text-xs text-slate-500 mt-2">Supported genres: {suggestedGenreHint}</p>

        <button
          onClick={getRecommendations}
          disabled={loading}
          className="mt-5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 px-5 py-2 rounded-lg font-semibold"
        >
          {loading ? "Finding best matches..." : "Recommend movies"}
        </button>

        {error && <p className="mt-4 text-red-300">{error}</p>}

        {results && (
          <div className="mt-8">
            <div className="bg-slate-900 border border-white/10 rounded-xl p-4 mb-6">
              <p className="text-sm text-slate-300">
                Cluster #{results.cluster?.cluster_id} | Dominant genres: {results.cluster?.profile?.dominant_genres?.join(", ") || "n/a"}
              </p>
              {results.search_analysis && (
                <p className="text-sm text-sky-300 mt-2">Search analysis: {results.search_analysis}</p>
              )}
              {results.system_notes && results.system_notes.length > 0 && (
                <p className="text-sm text-yellow-300 mt-2">Notes: {results.system_notes.join(" | ")}</p>
              )}
              <p className="text-xs text-slate-400 mt-1">
                LLM explanations: {results.rate_limited ? "fallback reasoning used" : "active"}
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {results.recommendations.map((rec) => (
                <div key={rec.movie_id} className="bg-slate-900 border border-white/10 rounded-xl p-4">
                  <h3 className="font-semibold">{rec.title}</h3>
                  <p className="text-xs text-slate-400 mt-1">{rec.genres}</p>
                  <p className="text-sm mt-2 text-green-400">Score: {rec.score}%</p>
                  <p className="text-sm text-slate-300">Estimated rating: {rec.estimated_rating}/5</p>
                  <p className="text-sm text-slate-200 mt-3">{rec.reason}</p>
                  <p className="text-xs text-slate-400 mt-2">{rec.summary}</p>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default PersonalPreferencePage
