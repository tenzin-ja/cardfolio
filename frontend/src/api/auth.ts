// Expected response from the backend's /auth/login endpoint.
type LoginResponse = {
  access_token: string
  token_type: 'bearer'
}
// Public account details returned by the backend.
// JSON sends the creation date as a string.
export type CurrentUser = {
  id: number
  email: string
  created_at: string
}

//this function gets called once the user attempts to sign in
//and sends the information to the backend which will verify
export async function login(
  email: string,
  password: string,
): Promise<string> {

  
    let response: Response

    try {
        //Sends email and password as a JSON
        //must first go through the vite proxy
        response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
            'Content-Type': 'application/json',
            },
            body: JSON.stringify({ email, password }),
        })
    } catch {
        throw new Error('Could not reach Cardfolio. Please try again.')
    }

    if (response.status === 401) {
        throw new Error('Incorrect email or password.')
    }

    if (!response.ok) {
        throw new Error('Could not log in. Please try again.')
    }

    const data: LoginResponse = await response.json()
        return data.access_token
    }

// Ask the backend which account belongs to this token.
// null means the token was rejected; other failures produce an error.
export async function getCurrentUser(
  accessToken: string,
): Promise<CurrentUser | null> {
  let response: Response

  try {
    response = await fetch('/api/auth/me', {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    })
  } catch {
    throw new Error('Could not reach Cardfolio. Please try again.')
  }

  // App can clear an invalid session when it receives null.
  if (response.status === 401) {
    return null
  }

  if (!response.ok) {
    throw new Error('Could not load your account. Please try again.')
  }

  return response.json()
}