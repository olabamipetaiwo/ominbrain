# Input check: Gemma-3-12B (gemma3:12b)

## Do all images reach the model? (prompt tokens; real v4 items)

| phase | images | image size | text only | tokens by images added | increment per added image |
|---|---|---|---|---|---|
| AIA | 1 | (728, 872) | 383 | {0: 383, 1: 678} | [295] |
| LIL | 1 | (728, 872) | 434 | {0: 434, 1: 728} | [294] |
| DSCR | 3 | (728, 872) | 541 | {0: 541, 1: 836, 2: 1120, 3: 1425} | [295, 284, 305] |

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