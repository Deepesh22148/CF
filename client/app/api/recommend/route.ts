import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
    const payload = await request.json();

    const fastApiUrl = process.env.FASTAPI_URL || "http://127.0.0.1:8000";
    const recommendationUrl = `${fastApiUrl}/recommendation/`;
    const response = await fetch(recommendationUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        ...payload,
      }),
    });

    const body = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { error: body.detail || "Backend error" },
        { status: response.status },
      );
    }

    return NextResponse.json(body);
  } catch (error) {
    console.error(error);
    return NextResponse.json(
      {
        status: 500,
        message: "Something went wrong while getting recommendations",
      },
      { status: 500 },
    );
  }
}
