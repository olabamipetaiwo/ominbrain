# Input check: Gemma-3-27B-bf16 (google/gemma-3-27b-it)

## Do all images reach the model? (prompt tokens; real v4 items)

| phase | images | image size | text only | tokens by images added | increment per added image |
|---|---|---|---|---|---|
| AIA | 1 | (728, 872) | 378 | {0: 378, 1: 656} | [278] |
| LIL | 1 | (728, 872) | 425 | {0: 425, 1: 708} | [283] |
| DSCR | 3 | (728, 872) | 540 | {0: 540, 1: 818, 2: 1089, 3: 1377} | [278, 271, 288] |

## Perception probes (same message format)

| probe | expected | answer | pass |
|---|---|---|---|
| colour_red | red | Red. | yes |
| colour_green | green | Green. | yes |
| colour_blue | blue | Blue. | yes |
| number_742 | 742 | 742 | yes |
| number_1905 | 1905 | 1905 | yes |
| three_images_order | red, green, blue | Red, green, blue | yes |
| two_images_second | blue | Blue | yes |
| real_slice_background | black | Black | yes |

8 of 8 probes passed.