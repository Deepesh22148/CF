"use client";

import PersonalLayout from "@/components/layout/PersonalLayout";
import React from "react";

const occupations = [
  "administrator","artist","doctor","educator","engineer","entertainment",
  "executive","healthcare","homemaker","lawyer","librarian","marketing",
  "none","other","programmer","retired","salesman","scientist",
  "student","technician","writer",
];

const genresList = [
  "Action","Adventure","Animation","Children's","Comedy","Crime",
  "Documentary","Drama","Fantasy","Film-Noir","Horror","Musical",
  "Mystery","Romance","Sci-Fi","Thriller","War","Western",
];

const ProfilePage = ({ user_id }: { user_id: string }) => {
  const [user, setUser] = React.useState<any>(null);
  const [editMode, setEditMode] = React.useState(false);
  const [loading, setLoading] = React.useState(false);

  const [form, setForm] = React.useState({
    name: "",
    age: "",
    occupation: "",
    gender: "",
    genres: [] as string[],
  });

  const fetchUser = async () => {
    const res = await fetch("/api/user/my-info", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id }),
    });

    const { body } = await res.json();

    if (res.ok) {
      setUser(body.data);
      setForm({
        name: body.data.name || "",
        age: body.data.age?.toString() || "",
        occupation: body.data.occupation || "",
        gender: body.data.gender || "",
        genres: body.data.genres || [],
      });
    }
  };

  React.useEffect(() => {
    fetchUser();
  }, []);

  const toggleGenre = (genre: string) => {
    setForm((prev) => ({
      ...prev,
      genres: prev.genres.includes(genre)
        ? prev.genres.filter((g) => g !== genre)
        : [...prev.genres, genre],
    }));
  };

  const handleUpdate = async () => {
    setLoading(true);

    const res = await fetch("/api/user/update-user", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        id: user_id,
        name: form.name,
        age: Number(form.age),
        occupation: form.occupation,
        gender: form.gender,
        genres: form.genres,
      }),
    });

    if (res.ok) {
      setEditMode(false);
      fetchUser();
    }

    setLoading(false);
  };

  return (
    <PersonalLayout user_id={user_id}>
      <div className="min-h-[calc(100vh-64px)] flex justify-center items-start p-6 text-slate-200">

        {/* CARD */}
        <div className="w-full max-w-2xl p-6 rounded-2xl bg-slate-900 border border-slate-700 shadow-lg">

          {/* HEADER */}
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold text-cyan-400">
              Your Profile
            </h2>

            <button
              onClick={() => setEditMode(!editMode)}
              className="px-4 py-1 text-sm rounded-md bg-slate-800 border border-slate-600 hover:border-cyan-400 transition"
            >
              {editMode ? "Cancel" : "Edit"}
            </button>
          </div>

          {/* VIEW MODE */}
          {!editMode && user && (
            <div className="space-y-4 text-slate-300">
              <p><span className="text-slate-100">Name:</span> {user.name}</p>
              <p><span className="text-slate-100">Age:</span> {user.age}</p>
              <p><span className="text-slate-100">Gender:</span> {user.gender}</p>
              <p><span className="text-slate-100">Occupation:</span> {user.occupation}</p>

              <div>
                <p className="text-slate-100 mb-2">Genres:</p>
                <div className="flex flex-wrap gap-2">
                  {user.genres?.map((g: string) => (
                    <span
                      key={g}
                      className="px-3 py-1 text-sm rounded-full bg-slate-800 border border-slate-600"
                    >
                      {g}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* EDIT MODE */}
          {editMode && (
            <div className="space-y-4">

              <input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="Name"
                className="w-full px-4 py-2 bg-slate-800 border border-slate-600 rounded-lg text-slate-100 focus:border-cyan-400 outline-none"
              />

              <input
                type="number"
                value={form.age}
                onChange={(e) => setForm({ ...form, age: e.target.value })}
                placeholder="Age"
                className="w-full px-4 py-2 bg-slate-800 border border-slate-600 rounded-lg text-slate-100 focus:border-cyan-400 outline-none"
              />

              {/* GENDER */}
              <div className="flex gap-2">
                {["male", "female", "other"].map((g) => (
                  <button
                    key={g}
                    onClick={() => setForm({ ...form, gender: g })}
                    className={`px-4 py-1 rounded-full border text-sm transition ${
                      form.gender === g
                        ? "bg-cyan-500 text-slate-900 border-cyan-500"
                        : "border-slate-600 text-slate-300 hover:border-cyan-400"
                    }`}
                  >
                    {g}
                  </button>
                ))}
              </div>

              {/* OCCUPATION */}
              <select
                value={form.occupation}
                onChange={(e) =>
                  setForm({ ...form, occupation: e.target.value })
                }
                className="w-full px-4 py-2 bg-slate-800 border border-slate-600 rounded-lg text-slate-100 focus:border-cyan-400 outline-none"
              >
                <option value="">Select occupation</option>
                {occupations.map((o) => (
                  <option key={o} value={o}>{o}</option>
                ))}
              </select>

              {/* GENRES */}
              <div className="flex flex-wrap gap-2">
                {genresList.map((g) => (
                  <button
                    key={g}
                    onClick={() => toggleGenre(g)}
                    className={`px-3 py-1 text-sm rounded-full border transition ${
                      form.genres.includes(g)
                        ? "bg-cyan-500 text-slate-900 border-cyan-500"
                        : "border-slate-600 text-slate-300 hover:border-cyan-400"
                    }`}
                  >
                    {g}
                  </button>
                ))}
              </div>

              <button
                onClick={handleUpdate}
                disabled={loading}
                className="w-full py-2 bg-cyan-500 text-slate-900 rounded-lg hover:bg-cyan-400 transition"
              >
                {loading ? "Updating..." : "Update Profile"}
              </button>

            </div>
          )}

        </div>
      </div>
    </PersonalLayout>
  );
};

export default ProfilePage;