# Input check: MedGemma-4B (medgemma:4b)

## Do all images reach the model? (prompt tokens; real v4 items)

| phase | images | image size | text only | tokens by images added | increment per added image |
|---|---|---|---|---|---|
| AIA | 1 | (728, 872) | 377 | {0: 377, 1: 675} | [298] |
| LIL | 1 | (728, 872) | 428 | {0: 428, 1: 719} | [291] |
| DSCR | 3 | (728, 872) | 534 | {0: 534, 1: 829, 2: 1114, 3: 1422} | [295, 285, 308] |

## Perception probes (same message format)

| probe | expected | answer | pass |
|---|---|---|---|
| colour_red | red | Red | yes |
| colour_green | green | Green | yes |
| colour_blue | blue | Blue | yes |
| number_742 | 742 | 742 | yes |
| number_1905 | 1905 | 1905 | yes |
| three_images_order | red, green, blue | red, green, blue | yes |
| two_images_second | blue | Blue | yes |
| real_slice_background | black | Black | yes |

8 of 8 probes passed.