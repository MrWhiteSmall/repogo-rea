// RepoGo original reconstruction from the observed request contract.
// Response shape and server search algorithm are deliberately NOT inferred.
export function createSearch(baseURL, fetcher = fetch) {
  return async function searchNotes(query) {
    const response = await fetcher(new URL('/api/notes/search', baseURL), {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({query}),
    });
    // Preserve the original client's behavior, including JSON error responses.
    return response.json();
  };
}
