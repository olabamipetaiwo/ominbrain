# Input check: Gemma-3-27B (gemma3:27b)

## Do all images reach the model? (prompt tokens; real v4 items)

| phase | images | image size | text only | tokens by images added | increment per added image |
|---|---|---|---|---|---|
| AIA | 1 | (728, 872) | 382 | {0: 382, 1: 673} | [291] |
| LIL | 1 | (728, 872) | 433 | {0: 433, 1: 725} | [292] |
| DSCR | 3 | (728, 872) | 541 | {0: 541, 1: 841, 2: 1121, 3: 1425} | [300, 280, 304] |

## Perception probes (same message format)

| probe | expected | answer | pass |
|---|---|---|---|
| colour_red | red | Red. | yes |
| colour_green | green | Green. | yes |
| colour_blue | blue | Blue. | yes |
| number_742 | 742 | 742 | yes |
| number_1905 | 1905 | 1905 | yes |
| three_images_order | red, green, blue | Red, Green, Blue | yes |
| two_images_second | blue | Blue | yes |
| real_slice_background | black | Black | yes |

8 of 8 probes passed.