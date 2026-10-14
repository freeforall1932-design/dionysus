# Cut lists and never-cut list

## English — cut

| Cut | Example → result |
|---|---|
| Pleasantries | "Sure! I'd be happy to help." → *(delete)* |
| Process commentary | "Let me check the file." → *(delete)* |
| Tool narration | "I ran the test suite." → *(delete)* |
| Meta-commentary | "I trimmed this for brevity." → *(delete)* |
| Qualifiers | "It is important to note that" → *(delete)* |
| Wordy connectives | "in order to" → "to" |
| Redundant framing | "The reason is that" → "Because" |
| False urgency | "Careful — don't skip this" → *(state the risk plainly)* |
| Hedged filler | "It seems like maybe" → *(state it, or drop it)* |
| Restating the question | *(delete)* |

## Indonesian — cut

| Potong | Contoh → hasil |
|---|---|
| Basa-basi | "Baik, saya akan membantu." → *(hapus)* |
| Narasi proses | "Mari saya cek filenya." → *(hapus)* |
| Narasi tool | "Saya sudah menjalankan test." → *(hapus)* |
| Komentar meta | "Saya ringkas agar hemat token." → *(hapus)* |
| Pengisi | "perlu diketahui bahwa", "dapat dikatakan" → *(hapus)* |
| Sambung panjang | "dengan tujuan untuk" → "untuk" |
| Bingkai ulang | "Alasannya adalah karena" → "Karena" |
| Urgensi palsu | "Hati-hati ya, jangan sampai" → *(nyatakan risikonya)* |

## Never cut

- Numbers, units, dates, magnitudes
- Names, identifiers, versions
- Citations and citation keys
- Genuine hedges: "may", "is associated with", "in this sample", "kemungkinan"
- Logical connectors that carry real meaning: therefore, because, however
- Code, commands, file paths, LaTeX
- Exact error strings
- The decision itself, and the reason for it

## Never invent abbreviations

The official caveman set is: `cfg` · `impl` · `req` · `res` · `fn`

If the user did not write the abbreviation, do not use it. **No `→` in prose** —
write "to", "becomes", "yields".
