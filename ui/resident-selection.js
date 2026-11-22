// Match the saved original identity and body even if the server reordered its catalogue.
export function residentSelection(residents, requested, boundCharacter, boundKind) {
  if (requested) return residents.find(row => row.id === requested);
  return residents.find(row => row.characterId === boundCharacter && row.bodyKind === boundKind) ?? residents[0];
}
