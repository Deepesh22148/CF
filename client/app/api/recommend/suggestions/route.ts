import { NextRequest, NextResponse } from "next/server";

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const q = searchParams.get("q")?.trim() || "";
    const limitRaw = Number(searchParams.get("limit") || "8");
    const limit = Number.isFinite(limitRaw)
      ? Math.max(1, Math.min(25, Math.floor(limitRaw)))
      : 8;

    if (!q) {
      return NextResponse.json({ suggestions: [] });
    }

    const fastApiUrl = process.env.FASTAPI_URL || "http://127.0.0.1:8000";
    const targetUrl = `${fastApiUrl}/recommendation/movie-suggestions?query=${encodeURIComponent(q)}&limit=${limit}`;

    const response = await fetch(targetUrl, {
      method: "GET",
    });
    const body = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { error: body.detail || "Backend error" },
        { status: response.status },
      );
    }

    return NextResponse.json({ suggestions: body.suggestions || [] });
  } catch (error) {
    console.error(error);
    return NextResponse.json(
      { error: "Something went wrong while fetching suggestions" },
      { status: 500 },
    );
  }
}
