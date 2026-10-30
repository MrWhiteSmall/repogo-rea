import{searchNotes as n}from"./chunks/search.js";export const routes=[{path:"/notes/:id"}];export async function findNotes(q){return n(q)}
