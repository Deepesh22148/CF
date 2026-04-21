import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    const authUrl = process.env.FASTAPI_URL + "/user/auth-user";

    const response = await fetch(authUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        name: body.name,
        password: body.password,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { error: data.error || "Backend error" },
        { status: response.status }
      );
    }

    return NextResponse.json(data);

  } catch (error) {
    console.error(error);
    return NextResponse.json(
      {
        error: "Something went wrong during authentication",
      },
      { status: 500 }
    );
  }
}