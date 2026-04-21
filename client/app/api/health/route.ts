import { NextResponse, NextRequest } from "next/server";

export async function GET(request: NextRequest) {
  try {
    const BASE_URL = process.env.FASTAPI_URL + "/health";
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
    return NextResponse.json({
      status: 500,
      message: "something went wrong while fetching the user details!",
    });
  }
}
