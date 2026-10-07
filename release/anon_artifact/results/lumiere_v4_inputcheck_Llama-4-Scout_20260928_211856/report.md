# Input check: Llama-4-Scout (llama4:scout)

## Do all images reach the model? (prompt tokens; real v4 items)

| phase | images | image size | text only | tokens by images added | increment per added image |
|---|---|---|---|---|---|
| AIA | 1 | (728, 872) | 384 | {0: 384, 1: 1854} | [1470] |
| LIL | 1 | (728, 872) | 438 | {0: 438, 1: 1903} | [1465] |
| DSCR | 3 | (728, 872) | 542 | {0: 542, 1: 2012, 2: 3468, 3: 4945} | [1470, 1456, 1477] |

## Perception probes (same message format)

| probe | expected | answer | pass |
|---|---|---|---|
| colour_red | red | Red. | yes |
| colour_green | green | Green. | yes |
| colour_blue | blue | Blue. | yes |
| number_742 | 742 | 742 | yes |
| number_1905 | 1905 | 1905 | yes |
| three_images_order | red, green, blue | red, green, blue | yes |
| two_images_second | blue | Blue. | yes |
| real_slice_background | black | black. | yes |

8 of 8 probes passed.