import { NextRequest, NextResponse } from "next/server";

// name , age , occupation
export async function POST(request: NextRequest) {
  try {
    const data = await request.json();

    const addUserUrl = process.env.FASTAPI_URL + "/user/add-user";
    const response = await fetch(addUserUrl, {
      method: "POST",
      body: JSON.stringify({
        ...data
      }),
    });

    const body = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { error: body.detail || "Backend error" },
        { status: response.status },
      );
    }

    return NextResponse.json({
      body,
    });
  } catch (error) {
    console.error(error);
    return NextResponse.json({
      status: 500,
      message: "Something went wrong while adding user",
    });
  }
}
