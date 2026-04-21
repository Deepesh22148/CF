import { NextResponse, NextRequest } from "next/server";

export async function GET(request: NextRequest) {
  try {
    const fastApiUrl = process.env.FASTAPI_URL || "http://127.0.0.1:8000";
    const BASE_URL = `${fastApiUrl}/health`;
    const response = await fetch(BASE_URL, {
      method: "GET",
    });

    const body = await response.json();
    if (body.status == 200) {
      return NextResponse.json(
        {
          status: body.status,
          detail: body.detail,
        },
        {
          status: 200,
        },
      );
    }
  } catch (error) {
    console.error(error);
    return NextResponse.json(
      {
        status: 500,
        message: "Failed to reach backend health endpoint",
      },
      { status: 500 },
    );
  }
}
