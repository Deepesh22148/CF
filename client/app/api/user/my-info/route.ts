import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
    const data = await request.json();

    const getUserUrl = process.env.FASTAPI_URL + "/user/get-user-details";

    const response = await fetch(getUserUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        ...data,
      }),
    });

    const body = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { error: body.detail || "Backend error" },
        { status: response.status }
      );
    }

    return NextResponse.json({
      body,
    });

  } catch (error) {
    console.error(error);
    return NextResponse.json(
      {
        status: 500,
        message: "Something went wrong while fetching user details",
      },
      { status: 500 }
    );
  }
}