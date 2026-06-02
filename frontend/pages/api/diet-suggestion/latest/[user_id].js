const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

export default async function handler(req, res) {
  if (req.method !== "GET") {
    return res.status(405).json({ message: "Only GET requests are allowed" });
  }

  const { user_id } = req.query;

  try {
    const backendResponse = await fetch(
      `${API_BASE_URL}/diet-suggestion/latest/${user_id}`,
      {
        headers: {
          Authorization: req.headers.authorization || "",
        },
      }
    );

    const data = await backendResponse.json();

    if (!backendResponse.ok) {
      return res.status(backendResponse.status).json(data);
    }

    return res.status(200).json(data);
  } catch (error) {
    return res.status(500).json({
      message: "Unable to fetch latest diet suggestion. Make sure backend is running.",
    });
  }
}
