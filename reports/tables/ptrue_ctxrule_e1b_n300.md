# P(True) context x rule probe — 300 steps (150 incorrect / 150 correct), 11 conditions

Conditions run: `C0/R0`, `C1/R0`, `C2/R0`, `C3/R0`, `C4/R0`, `C5/R0`, `C6/R0`, `C3/R1`, `C3/R2`, `C3/R3`, `C0/R2`.  Baseline = `C3/R0` (the production P(True) prompt).

- context: **C0** task + action; **C1** task + last observation + action; **C2** task + full history + action; **C3** task + full history + reasoning + action (production); **C4** task + full history + reasoning, no action; **C5** production + the OUTCOME of the action (pre-hindsight); **C6** production + outcome + the agent's next step (pre-hindsight, full)
- rule: **R0** none; **R1** generic rubric; **R2** targeted (repeat); **R3** decoy (irrelevant)

U = P(No) renormalized over {Yes,No} = 1 - P(True); higher = more uncertain the step is right. **Delta = mean U(incorrect) - mean U(correct)** is the separation. Unparsed cells are excluded, never imputed.

_Showing the 24 steps with the largest |U(C5) − U(production)| shift, of 300 total — the full matrix is in the CSV._

## Steps

Per step: the 3-judge ensemble vote (the label), then P(Yes) — the model's P(True) — in each condition. `x` = the first token carried no Yes/No mass (unparsed, excluded from every aggregate, never imputed).

### 1. pick_clean_then_place_in_recep-ButterKnife-None-CounterTop-8/trial_T20190909_105559_983897 — step 42 — judge: **INCORRECT** (3/3 votes incorrect), stratum `inadmissible`

- task: put a clean butterknife in countertop.
- action: `take butterknife 3 from countertop 4`  (repeats a prior action)
- reasoning: The task is to put a clean butterknife on the countertop. I previously picked up the butterknife and moved it back to countertop 4, but repeated attempts resulted in the same state, suggesting the environment might require a specific sequence or that the item needs to be cleaned first. Since there i …

| judge | vote | reason |
|---|---|---|
| DeepSeek-V4-Pro | incorrect | Trying to take the butterknife while at the sinkbasin without it being there is  |
| gpt-5.6-sol | incorrect | Trying to take the knife from the countertop while at the sink cannot succeed. |
| grok-4.3 | incorrect | Attempting to take the knife while at the sink fails and wastes a step. |

| C0/R0 | C1/R0 | C2/R0 | C3/R0 | C4/R0 | C5/R0 | C6/R0 | C3/R1 | C3/R2 | C3/R3 | C0/R2 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.165 | 0.128 | 0.090 | 0.852 | 0.835 | 0.049 | 0.501 | 0.349 | 0.408 | 0.652 | 0.066 |

### 2. pick_clean_then_place_in_recep-Ladle-None-CounterTop-8/trial_T20190909_121908_219603 — step 33 — judge: **INCORRECT** (3/3 votes incorrect), stratum `inadmissible`

- task: put a clean ladle in countertop.
- action: `go to cabinet 9`
- reasoning: I have searched many drawers and cabinets but haven't found a ladle yet. The task requires putting a clean ladle on the countertop. Since I haven't found it in the standard storage locations (drawers 1-7, cabinets 1-8), I need to check the remaining cabinets (9-18). I will proceed to check cabinet 9 …

| judge | vote | reason |
|---|---|---|
| DeepSeek-V4-Pro | incorrect | Attempting to go to cabinet 9 fails with no observation, indicating an invalid o |
| gpt-5.6-sol | incorrect | The attempt to go to cabinet 9 fails and yields no useful exploration. |
| grok-4.3 | incorrect | Going to cabinet 9 produces nothing and adds no new information. |

| C0/R0 | C1/R0 | C2/R0 | C3/R0 | C4/R0 | C5/R0 | C6/R0 | C3/R1 | C3/R2 | C3/R3 | C0/R2 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.706 | 0.531 | 0.531 | 0.775 | 0.849 | 0.101 | 0.205 | 0.755 | 0.732 | 0.652 | 0.640 |

### 3. pick_cool_then_place_in_recep-Bowl-None-Cabinet-20/trial_T20190909_112912_154874 — step 14 — judge: **INCORRECT** (3/3 votes incorrect), stratum `inadmissible`

- task: put a cool bowl in cabinet.
- action: `open cabinet 1`  (repeats a prior action)
- reasoning: The task is to "put a cool bowl in cabinet." I have already placed bowl 1 into cabinet 1. However, the instruction specifies a "cool" bowl. In this environment, objects can be cooled using the fridge. Currently, bowl 1 is inside cabinet 1 and cannot be interacted with directly while closed. To make  …

| judge | vote | reason |
|---|---|---|
| DeepSeek-V4-Pro | incorrect | Trying to open cabinet 1 while at the fridge is irrelevant and indicates a locat |
| gpt-5.6-sol | incorrect | Trying to open the distant cabinet from the fridge cannot help retrieve or cool  |
| grok-4.3 | incorrect | Trying to open the cabinet while at the fridge is an invalid action that does no |

| C0/R0 | C1/R0 | C2/R0 | C3/R0 | C4/R0 | C5/R0 | C6/R0 | C3/R1 | C3/R2 | C3/R3 | C0/R2 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.195 | 0.003 | 0.002 | 0.818 | 0.706 | 0.056 | 0.089 | 0.593 | 0.270 | 0.532 | 0.328 |

### 4. pick_cool_then_place_in_recep-Plate-None-CounterTop-1/trial_T20190906_205324_559361 — step 25 — judge: **INCORRECT** (3/3 votes incorrect), stratum `inadmissible`

- task: cool some plate and put it in countertop.
- action: `cool pan 1 with fridge 1`
- reasoning: The task is to "cool some plate and put it in countertop." I have successfully cooled a bowl and placed it on the countertop. However, the object was a bowl, not a plate. Looking at my inventory, I am holding pan 1. In this environment, pans are often treated as plates or similar flat cookware. Sinc …

| judge | vote | reason |
|---|---|---|
| DeepSeek-V4-Pro | incorrect | Attempting to cool a pan with the fridge while not at the fridge is an invalid a |
| gpt-5.6-sol | incorrect | Attempting to cool the irrelevant pan does not advance the task. |
| grok-4.3 | incorrect | Attempting to cool the pan is irrelevant to the plate task. |

| C0/R0 | C1/R0 | C2/R0 | C3/R0 | C4/R0 | C5/R0 | C6/R0 | C3/R1 | C3/R2 | C3/R3 | C0/R2 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.074 | 0.133 | 0.500 | 0.706 | 0.379 | 0.021 | 0.096 | 0.562 | 0.593 | 0.623 | 0.102 |

### 5. pick_two_obj_and_place-CreditCard-None-Dresser-311/trial_T20190907_201917_045715 — step 3 — judge: **INCORRECT** (3/3 votes incorrect), stratum `inadmissible`

- task: put two creditcard in dresser.
- action: `take creditcard 1 from sidetable 1`
- reasoning: The task is to put two credit cards in the dresser. I have identified that there are two credit cards (creditcard 1 and creditcard 2) on sidetable 1, and an empty space on dresser 1. To achieve the goal, I first need to retrieve the credit cards from the sidetable. I will start by taking the first c …

| judge | vote | reason |
|---|---|---|
| DeepSeek-V4-Pro | incorrect | Attempting to take creditcard 1 from sidetable 1 while at dresser 1 is impossibl |
| gpt-5.6-sol | incorrect | Attempting to take a credit card from the sidetable while at the dresser cannot  |
| grok-4.3 | incorrect | Attempting to take an object from the wrong location after leaving it. |

| C0/R0 | C1/R0 | C2/R0 | C3/R0 | C4/R0 | C5/R0 | C6/R0 | C3/R1 | C3/R2 | C3/R3 | C0/R2 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.450 | 0.095 | 0.441 | 0.889 | 0.698 | 0.068 | 0.446 | 0.502 | 0.866 | 0.795 | 0.512 |

### 6. pick_two_obj_and_place-Glassbottle-None-Shelf-1/trial_T20190907_122204_941737 — step 5 — judge: **INCORRECT** (3/3 votes incorrect), stratum `inadmissible`

- task: find two glassbottle and put them in shelf.
- action: `take glassbottle 2 from countertop 1`
- reasoning: I have successfully picked up glassbottle 1. The task requires finding two glass bottles and putting them on a shelf. I am currently holding one bottle. I need to pick up the second bottle (glassbottle 2), which is also on countertop 1, before moving to a shelf. Therefore, my next step is to take gl …

| judge | vote | reason |
|---|---|---|
| DeepSeek-V4-Pro | incorrect | Attempting to take glassbottle 2 while already holding glassbottle 1 fails and p |
| gpt-5.6-sol | incorrect | Attempting to take the second bottle while already carrying one fails and makes  |
| grok-4.3 | incorrect | Attempting to take a second item while already holding one is invalid and yields |

| C0/R0 | C1/R0 | C2/R0 | C3/R0 | C4/R0 | C5/R0 | C6/R0 | C3/R1 | C3/R2 | C3/R3 | C0/R2 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.438 | 0.147 | 0.871 | 0.993 | 0.877 | 0.026 | 0.183 | 0.963 | 0.982 | 0.866 | 0.442 |

### 7. pick_two_obj_and_place-ToiletPaper-None-Drawer-423/trial_T20190907_111251_461099 — step 32 — judge: **INCORRECT** (3/3 votes incorrect), stratum `inadmissible`

- task: put two toiletpaper in drawer.
- action: `move toiletpaper 2 to drawer 1`
- reasoning: I have successfully placed one toiletpaper (toiletpaper 1) into drawer 1. I am currently holding toiletpaper 2 at the location of toilet 1. To complete the task, I need to place this second toiletpaper into the same drawer. Therefore, I will move toiletpaper 2 to drawer 1.

| judge | vote | reason |
|---|---|---|
| DeepSeek-V4-Pro | incorrect | Attempting to move toiletpaper 2 to drawer 1 from a distance fails; going to the |
| gpt-5.6-sol | incorrect | Trying to move the toilet paper to a distant drawer fails and does not advance t |
| grok-4.3 | incorrect | Attempting move without being at the drawer is invalid and fails. |

| C0/R0 | C1/R0 | C2/R0 | C3/R0 | C4/R0 | C5/R0 | C6/R0 | C3/R1 | C3/R2 | C3/R3 | C0/R2 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.235 | 0.310 | 0.923 | 0.986 | 0.797 | 0.049 | 0.651 | 0.940 | 0.977 | 0.971 | 0.469 |

### 8. pick_clean_then_place_in_recep-Spatula-None-DiningTable-4/trial_T20190909_002804_564168 — step 4 — judge: **INCORRECT** (3/3 votes incorrect), stratum `loop`

- task: clean some spatula and put it in diningtable.
- action: `examine drawer 2`
- reasoning: I am currently at drawer 2. The task requires me to clean a spatula and put it on the dining table. I have not yet found a spatula. Drawer 1 contained only a saltshaker, so I need to check other locations. Since I am already at drawer 2, examining its contents is the logical next step to see if it c …

| judge | vote | reason |
|---|---|---|
| DeepSeek-V4-Pro | incorrect | Examining a closed drawer before opening it is redundant and adds no new informa |
| gpt-5.6-sol | incorrect | Examining the closed drawer adds no useful information before opening it. |
| grok-4.3 | incorrect | Examining a closed drawer provides no new information and does not progress the  |

| C0/R0 | C1/R0 | C2/R0 | C3/R0 | C4/R0 | C5/R0 | C6/R0 | C3/R1 | C3/R2 | C3/R3 | C0/R2 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.178 | 0.107 | 0.148 | 0.815 | 0.889 | 0.107 | 0.681 | 0.799 | 0.623 | 0.707 | 0.152 |

### 9. pick_cool_then_place_in_recep-Bowl-None-Cabinet-20/trial_T20190909_112912_154874 — step 16 — judge: **INCORRECT** (3/3 votes incorrect), stratum `loop`

- task: put a cool bowl in cabinet.
- action: `open cabinet 1`  (repeats a prior action)
- reasoning: The task is to "put a cool bowl in cabinet". I have already placed the bowl in cabinet 1 and closed it. However, the adjective "cool" suggests the bowl should be cold. To achieve this, I need to place the bowl inside the fridge 1, which will cool it down. Since the bowl is currently inside cabinet 1 …

| judge | vote | reason |
|---|---|---|
| DeepSeek-V4-Pro | incorrect | Another repeated failed attempt to open the cabinet from the fridge shows loopin |
| gpt-5.6-sol | incorrect | A third identical failed attempt is unproductive looping. |
| grok-4.3 | incorrect | Further repetition of the same failed action shows no progress. |

| C0/R0 | C1/R0 | C2/R0 | C3/R0 | C4/R0 | C5/R0 | C6/R0 | C3/R1 | C3/R2 | C3/R3 | C0/R2 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.195 | 0.319 | 0.000 | 0.835 | 0.693 | 0.095 | 0.297 | 0.623 | 0.532 | 0.679 | 0.328 |

### 10. pick_heat_then_place_in_recep-Cup-None-Cabinet-22/trial_T20190907_173251_960848 — step 48 — judge: **INCORRECT** (3/3 votes incorrect), stratum `loop`

- task: put a hot cup in cabinet.
- action: `take mug 1 from cabinet 1`  (repeats a prior action)
- reasoning: The mug in the cabinet is cold because it was never heated. To fulfill the task "put a hot cup in cabinet", I must first heat the mug. The available commands show that there is an apple inside the microwave, but no mug. I need to retrieve the mug from the cabinet, place it in the microwave to heat i …

| judge | vote | reason |
|---|---|---|
| DeepSeek-V4-Pro | incorrect | Trying to take the mug while at the microwave is impossible. |
| gpt-5.6-sol | incorrect | Trying to take the mug from a distant cabinet while at the microwave cannot work |
| grok-4.3 | incorrect | Failed take attempt is part of the loop. |

| C0/R0 | C1/R0 | C2/R0 | C3/R0 | C4/R0 | C5/R0 | C6/R0 | C3/R1 | C3/R2 | C3/R3 | C0/R2 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.022 | 0.006 | 0.063 | 0.772 | 0.699 | 0.034 | 0.504 | 0.410 | 0.224 | 0.533 | 0.011 |

### 11. pick_two_obj_and_place-AlarmClock-None-Dresser-305/trial_T20190907_165826_194855 — step 14 — judge: **INCORRECT** (3/3 votes incorrect), stratum `loop`

- task: put two alarmclock in dresser.
- action: `go to desk 1`  (repeats a prior action)
- reasoning: I have successfully picked up alarmclock 1 from desk 1. The task requires putting two alarm clocks into a dresser. I still need to pick up a second alarm clock. Looking at the available commands, I can go back to desk 1 where alarmclock 2 and alarmclock 3 are located. I will go to desk 1 to retrieve …

| judge | vote | reason |
|---|---|---|
| DeepSeek-V4-Pro | incorrect | Attempting to go to the desk while already there is a redundant action. |
| gpt-5.6-sol | incorrect | Going to the desk while already there does nothing and adds no benefit. |
| grok-4.3 | incorrect | Going to desk 1 again produces no new information or progress. |

| C0/R0 | C1/R0 | C2/R0 | C3/R0 | C4/R0 | C5/R0 | C6/R0 | C3/R1 | C3/R2 | C3/R3 | C0/R2 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.148 | 0.005 | 0.011 | 0.852 | 0.850 | 0.078 | 0.188 | 0.798 | 0.623 | 0.706 | 0.284 |

### 12. pick_two_obj_and_place-CreditCard-None-Safe-323/trial_T20190907_001129_214240 — step 7 — judge: **INCORRECT** (3/3 votes incorrect), stratum `loop`

- task: put two creditcard in safe.
- action: `go to desk 1`  (repeats a prior action)
- reasoning: I have successfully picked up creditcard 2. The task requires putting two credit cards in the safe. Looking at my history, I saw creditcard 3 and creditcard 2 on desk 1. I have taken creditcard 2, but I still need to take creditcard 3. Therefore, my next step is to go back to desk 1 to retrieve cred …

| judge | vote | reason |
|---|---|---|
| DeepSeek-V4-Pro | incorrect | Repeating 'go to desk 1' while already there adds no new information and wastes  |
| gpt-5.6-sol | incorrect | Going to the desk while already there produces no progress or new information. |
| grok-4.3 | incorrect | Returning to desk 1 is redundant since the agent is already there and yields no  |

| C0/R0 | C1/R0 | C2/R0 | C3/R0 | C4/R0 | C5/R0 | C6/R0 | C3/R1 | C3/R2 | C3/R3 | C0/R2 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.133 | 0.000 | 0.002 | 0.902 | 0.793 | 0.131 | 0.321 | 0.778 | 0.649 | 0.704 | 0.382 |

### 13. pick_two_obj_and_place-SprayBottle-None-GarbageCan-419/trial_T20190908_164236_518264 — step 4 — judge: **INCORRECT** (3/3 votes incorrect), stratum `loop`

- task: put two spraybottle in garbagecan.
- action: `go to sidetable 1`  (repeats a prior action)
- reasoning: I have successfully picked up spraybottle 1. The task requires two spray bottles in the garbage can, and I see spraybottle 2 is still on sidetable 1. My next step is to retrieve spraybottle 2 from the same location. Therefore, I need to go back to sidetable 1 to pick it up.

| judge | vote | reason |
|---|---|---|
| DeepSeek-V4-Pro | incorrect | Repeating 'go to sidetable 1' while already there adds no new information or pro |
| gpt-5.6-sol | incorrect | Going to the side table while already there produces no new information or progr |
| grok-4.3 | incorrect | Repeating go to sidetable 1 produces no new information or progress. |

| C0/R0 | C1/R0 | C2/R0 | C3/R0 | C4/R0 | C5/R0 | C6/R0 | C3/R1 | C3/R2 | C3/R3 | C0/R2 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.274 | 0.011 | 0.011 | 0.903 | 0.816 | 0.128 | 0.253 | 0.836 | 0.678 | 0.562 | 0.190 |

### 14. pick_two_obj_and_place-SprayBottle-None-Toilet-402/trial_T20190910_222914_814642 — step 24 — judge: **INCORRECT** (3/3 votes incorrect), stratum `loop`

- task: find two spraybottle and put them in toilet.
- action: `take spraybottle 1 from garbagecan 1`
- reasoning: I have located both spray bottles: spraybottle 1 is in garbagecan 1, and spraybottle 2 is in cabinet 3. My previous attempt to take spraybottle 2 failed ("Nothing happens"), likely because the command syntax or interaction type was incorrect for that specific object/location combination. I need to t …

| judge | vote | reason |
|---|---|---|
| DeepSeek-V4-Pro | incorrect | Attempting to take spraybottle 1 without being at garbagecan 1 is ineffective. |
| gpt-5.6-sol | incorrect | Attempting to take the garbage-can bottle while at cabinet 3 cannot succeed. |
| grok-4.3 | incorrect | Attempting to take while inventory is full repeats failure. |

| C0/R0 | C1/R0 | C2/R0 | C3/R0 | C4/R0 | C5/R0 | C6/R0 | C3/R1 | C3/R2 | C3/R3 | C0/R2 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.281 | 0.245 | 0.784 | 0.940 | 0.671 | 0.044 | 0.502 | 0.798 | 0.731 | 0.798 | 0.438 |

### 15. pick_two_obj_and_place-Watch-None-Dresser-205/trial_T20190907_182211_592010 — step 4 — judge: **INCORRECT** (3/3 votes incorrect), stratum `loop`

- task: put two watch in dresser.
- action: `go to diningtable 1`  (repeats a prior action)
- reasoning: I have successfully picked up watch 1. The task is to put two watches in the dresser. I still need to acquire watch 2, which is currently on diningtable 1. Therefore, my next step is to go back to the dining table to pick up the second watch.

| judge | vote | reason |
|---|---|---|
| DeepSeek-V4-Pro | incorrect | Attempting to go to the diningtable while already there is a redundant action wi |
| gpt-5.6-sol | incorrect | The agent is already at the dining table, so this action adds no benefit. |
| grok-4.3 | incorrect | Repeating go to diningtable 1 produces no new effect or progress. |

| C0/R0 | C1/R0 | C2/R0 | C3/R0 | C4/R0 | C5/R0 | C6/R0 | C3/R1 | C3/R2 | C3/R3 | C0/R2 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.183 | 0.018 | 0.000 | 0.912 | 0.796 | 0.070 | 0.074 | 0.818 | 0.619 | 0.753 | 0.305 |

### 16. pick_two_obj_and_place-Watch-None-Dresser-205/trial_T20190907_182211_592010 — step 5 — judge: **INCORRECT** (3/3 votes incorrect), stratum `loop`

- task: put two watch in dresser.
- action: `go to diningtable 1`  (repeats a prior action)
- reasoning: I have picked up watch 1. The task is to put two watches in the dresser. I still need to pick up watch 2 from diningtable 1 and then place both watches into dresser 1. My immediate next step is to go back to diningtable 1 to retrieve watch 2.

| judge | vote | reason |
|---|---|---|
| DeepSeek-V4-Pro | incorrect | Repeating the same 'go to diningtable' action again is unhelpful looping. |
| gpt-5.6-sol | incorrect | This repeats an ineffective move to the current location. |
| grok-4.3 | incorrect | Repeating go to diningtable 1 produces no new effect or progress. |

| C0/R0 | C1/R0 | C2/R0 | C3/R0 | C4/R0 | C5/R0 | C6/R0 | C3/R1 | C3/R2 | C3/R3 | C0/R2 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.202 | 0.244 | 0.001 | 0.796 | 0.768 | 0.087 | 0.234 | 0.752 | 0.385 | 0.651 | 0.305 |

### 17. pick_two_obj_and_place-CreditCard-None-Dresser-311/trial_T20190907_201917_045715 — step 15 — judge: **INCORRECT** (3/3 votes incorrect), stratum `other`

- task: put two creditcard in dresser.
- action: `move creditcard 1 to dresser 1`
- reasoning: I have successfully picked up creditcard 1 and am currently holding it. The task requires putting two credit cards into the dresser. Since I can only carry one item at a time (based on previous attempts to pick up the second card while holding the first failing), I must first place creditcard 1 into …

| judge | vote | reason |
|---|---|---|
| DeepSeek-V4-Pro | incorrect | Trying to move creditcard 1 to dresser 1 while not at dresser 1 is impossible an |
| gpt-5.6-sol | incorrect | Trying to move the first card to the dresser while not at the dresser fails. |
| grok-4.3 | incorrect | Trying to move an object while not at the target location fails and adds no valu |

| C0/R0 | C1/R0 | C2/R0 | C3/R0 | C4/R0 | C5/R0 | C6/R0 | C3/R1 | C3/R2 | C3/R3 | C0/R2 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.654 | 0.636 | 0.069 | 0.880 | 0.657 | 0.089 | 0.679 | 0.777 | 0.777 | 0.677 | 0.777 |

### 18. pick_two_obj_and_place-CreditCard-None-Dresser-311/trial_T20190907_201917_045715 — step 6 — judge: **INCORRECT** (3/3 votes incorrect), stratum `other`

- task: put two creditcard in dresser.
- action: `take creditcard 2 from sidetable 1`
- reasoning: I have successfully picked up creditcard 1. The task requires putting two credit cards into the dresser. I still need to pick up the second credit card (creditcard 2) from the sidetable. Since I am currently at the sidetable, I should take creditcard 2 next.

| judge | vote | reason |
|---|---|---|
| DeepSeek-V4-Pro | incorrect | The observation 'Nothing happens' suggests a failed attempt to take creditcard 2 |
| gpt-5.6-sol | incorrect | Attempting to pick up the second card while already carrying the first fails and |
| grok-4.3 | incorrect | Trying to take a second item while already holding one and before placing the fi |

| C0/R0 | C1/R0 | C2/R0 | C3/R0 | C4/R0 | C5/R0 | C6/R0 | C3/R1 | C3/R2 | C3/R3 | C0/R2 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.469 | 0.095 | 0.777 | 0.904 | 0.751 | 0.084 | 0.651 | 0.818 | 0.816 | 0.651 | 0.474 |

### 19. pick_two_obj_and_place-Glassbottle-None-Shelf-1/trial_T20190907_122204_941737 — step 10 — judge: **INCORRECT** (3/3 votes incorrect), stratum `other`

- task: find two glassbottle and put them in shelf.
- action: `move glassbottle 2 to shelf 1`
- reasoning: I have already placed glassbottle 1 on shelf 1. I am currently holding glassbottle 2, which was picked up from countertop 1. The task requires putting two glass bottles on the shelf. To complete this, I need to move glassbottle 2 to one of the shelves. Shelf 1 is a valid location as it already conta …

| judge | vote | reason |
|---|---|---|
| DeepSeek-V4-Pro | incorrect | Attempting to move glassbottle 2 to shelf 1 without being at the shelf fails and |
| gpt-5.6-sol | incorrect | Trying to move the bottle to the shelf while not at the shelf fails and adds no  |
| grok-4.3 | incorrect | Issuing a move action while not at the shelf produces no effect and wastes a ste |

| C0/R0 | C1/R0 | C2/R0 | C3/R0 | C4/R0 | C5/R0 | C6/R0 | C3/R1 | C3/R2 | C3/R3 | C0/R2 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.614 | 0.636 | 0.997 | 0.998 | 0.938 | 0.050 | 0.706 | 0.818 | 0.974 | 0.967 | 0.531 |

### 20. pick_two_obj_and_place-Knife-None-Drawer-18/trial_T20190907_065232_689984 — step 30 — judge: **INCORRECT** (3/3 votes incorrect), stratum `other`

- task: find two knife and put them in drawer.
- action: `move knife 1 to drawer 4`
- reasoning: I have successfully picked up knife 1. Knife 2 is already inside drawer 4. The task requires putting two knives in a drawer. Since knife 2 is already in drawer 4, I just need to put knife 1 into the same drawer (drawer 4) to satisfy the condition of having two knives in a drawer. Therefore, I will m …

| judge | vote | reason |
|---|---|---|
| DeepSeek-V4-Pro | incorrect | Attempting to move knife 1 to drawer 4 without being at the drawer fails and is  |
| gpt-5.6-sol | incorrect | Attempting to place the knife in a distant drawer fails because the agent has no |
| grok-4.3 | incorrect | Attempting to move knife without being at drawer location fails. |

| C0/R0 | C1/R0 | C2/R0 | C3/R0 | C4/R0 | C5/R0 | C6/R0 | C3/R1 | C3/R2 | C3/R3 | C0/R2 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.245 | 0.074 | 0.946 | 0.980 | 0.847 | 0.022 | 0.562 | 0.836 | 0.818 | 0.958 | 0.327 |

### 21. pick_two_obj_and_place-Newspaper-None-Drawer-224/trial_T20190911_101248_326533 — step 25 — judge: **INCORRECT** (3/3 votes incorrect), stratum `other`

- task: put two newspaper in drawer.
- action: `take newspaper 2 from sofa 1`
- reasoning: I am currently holding newspaper 1. Newspaper 2 is on sofa 1. The task is to put two newspapers in a drawer. I need to pick up newspaper 2 first, then take both to a drawer and place them inside. Since I am already at sofa 1 (implied by the last successful 'go' command showing items on sofa), I shou …

| judge | vote | reason |
|---|---|---|
| DeepSeek-V4-Pro | incorrect | Attempting to take newspaper 2 from sofa 1 fails, likely due to a perception or  |
| gpt-5.6-sol | incorrect | Attempting to take newspaper 2 while already carrying newspaper 1 predictably fa |
| grok-4.3 | incorrect | Failed take attempt while inventory is full, no benefit. |

| C0/R0 | C1/R0 | C2/R0 | C3/R0 | C4/R0 | C5/R0 | C6/R0 | C3/R1 | C3/R2 | C3/R3 | C0/R2 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.593 | 0.660 | 0.678 | 0.865 | 0.582 | 0.056 | 0.101 | 0.731 | 0.680 | 0.777 | 0.651 |

### 22. pick_two_obj_and_place-SoapBar-None-GarbageCan-418/trial_T20190909_055649_717880 — step 4 — judge: **INCORRECT** (3/3 votes incorrect), stratum `other`

- task: find two soapbar and put them in garbagecan.
- action: `take soapbar 3 from countertop 1`
- reasoning: I have already picked up soapbar 2. The task requires finding two soapbars and putting them in the garbage can. I am currently holding one soapbar (soapbar 2) and need to get another one. Looking at my previous observation of countertop 1, there is also a soapbar 3 available there. Since I am still  …

| judge | vote | reason |
|---|---|---|
| DeepSeek-V4-Pro | incorrect | Attempting to take soapbar 3 without holding it fails, but the action is a repea |
| gpt-5.6-sol | incorrect | Attempting to take the second soapbar while already holding one fails and does n |
| grok-4.3 | incorrect | Attempt to take the second soapbar fails with no effect due to incorrect positio |

| C0/R0 | C1/R0 | C2/R0 | C3/R0 | C4/R0 | C5/R0 | C6/R0 | C3/R1 | C3/R2 | C3/R3 | C0/R2 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.010 | 0.006 | 0.727 | 0.792 | 0.588 | 0.031 | 0.167 | 0.731 | 0.836 | 0.756 | 0.007 |

### 23. pick_clean_then_place_in_recep-Fork-None-Drawer-8/trial_T20190908_132152_999725 — step 7 — judge: **correct** (0/3 votes incorrect), stratum `plain`

- task: clean some fork and put it in drawer.
- action: `go to countertop 3`
- reasoning: The goal is to clean a fork and put it in a drawer. I have not yet found a fork or a knife (which are often used interchangeably for cleaning tasks like scraping, but specifically I need a fork). Looking at the environment history, I haven't seen any forks listed on countertops or cabinets yet. Howe …

| judge | vote | reason |
|---|---|---|
| DeepSeek-V4-Pro | correct | Going to countertop 3 continues the search and successfully finds a fork. |
| gpt-5.6-sol | correct | Searching this countertop successfully locates the required fork. |
| grok-4.3 | correct | Exploring countertop 3 successfully locates a fork. |

| C0/R0 | C1/R0 | C2/R0 | C3/R0 | C4/R0 | C5/R0 | C6/R0 | C3/R1 | C3/R2 | C3/R3 | C0/R2 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.219 | 0.118 | 0.074 | 0.151 | 0.148 | 0.904 | 0.798 | 0.183 | 0.120 | 0.134 | 0.302 |

### 24. pick_cool_then_place_in_recep-Egg-None-Microwave-24/trial_T20190908_234112_645480 — step 17 — judge: **correct** (0/3 votes incorrect), stratum `plain`

- task: put a cool egg in microwave.
- action: `go to diningtable 1`
- reasoning: I need to put an egg in the microwave. Currently, I am at drawer 3. The fridge contains potatoes and tomatoes, but no eggs. Since the eggs are not in the fridge or the previously checked drawers/cabinets/countertops, they might be in another location like cabinet 6-23 or drawer 4. However, looking a …

| judge | vote | reason |
|---|---|---|
| DeepSeek-V4-Pro | correct | Going to the dining table is a good move as it often holds food items. |
| gpt-5.6-sol | correct | Going to the dining table successfully locates the target egg. |
| grok-4.3 | correct | Going to the diningtable examines a plausible location and finds the egg. |

| C0/R0 | C1/R0 | C2/R0 | C3/R0 | C4/R0 | C5/R0 | C6/R0 | C3/R1 | C3/R2 | C3/R3 | C0/R2 |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.006 | 0.001 | 0.041 | 0.231 | 0.148 | 0.903 | 0.679 | 0.247 | 0.151 | 0.150 | 0.016 |

## Separation per condition

AUROC (positive class = incorrect) is the ranking read — unlike Delta it is immune to the scale shifts that move mean U between contexts. CI = 95%, trajectory-clustered bootstrap (episodes resampled with their steps).

| condition | what changed | mean U inc | mean U cor | **Delta** | AUROC [95% CI] | sat | n | unparsed |
|---|---|---|---|---|---|---|---|---|
| **C0/R0** | task + action | 0.736 | 0.725 | **0.010** | 0.512 [0.438, 0.586] | 0 | 300 | 0 |
| **C1/R0** | task + last observation + action | 0.790 | 0.640 | **0.150** | 0.622 [0.555, 0.685] | 1 | 300 | 0 |
| **C2/R0** | task + full history + action | 0.800 | 0.558 | **0.242** | 0.697 [0.637, 0.755] | 9 | 300 | 0 |
| **C3/R0** | production prompt | 0.491 | 0.243 | **0.248** | 0.741 [0.675, 0.801] | 25 | 300 | 0 |
| **C4/R0** | task + full history + reasoning, no action | 0.488 | 0.259 | **0.229** | 0.740 [0.673, 0.798] | 13 | 300 | 0 |
| **C5/R0** | production + the OUTCOME of the action (pre-hindsight) | 0.684 | 0.288 | **0.396** | 0.813 [0.756, 0.865] | 12 | 300 | 0 |
| **C6/R0** | production + outcome + the agent's next step (pre-hindsight, full) | 0.693 | 0.394 | **0.299** | 0.845 [0.799, 0.888] | 0 | 300 | 0 |
| **C3/R1** | generic rubric rule | 0.579 | 0.254 | **0.325** | 0.804 [0.746, 0.853] | 18 | 300 | 0 |
| **C3/R2** | targeted (repeat) rule | 0.713 | 0.347 | **0.366** | 0.813 [0.753, 0.866] | 17 | 300 | 0 |
| **C3/R3** | decoy (irrelevant) rule | 0.575 | 0.333 | **0.242** | 0.728 [0.661, 0.789] | 1 | 300 | 0 |
| **C0/R2** | targeted (repeat) rule on task + action | 0.687 | 0.661 | **0.026** | 0.531 [0.455, 0.603] | 0 | 300 | 0 |

## Paired per-step shift vs `C3/R0`

Median per-step U difference and how many paired steps moved which way. At this n the sign count is the evidence: a small median with 18/20 in one direction is a real shift; a large median with 11/20 is one or two outliers.

| condition | median dU | down | up | n | median dU (inc) | median dU (cor) |
|---|---|---|---|---|---|---|
| C0/R0 | 0.339 | 44 | 256 | 300 | 0.206 | 0.544 |
| C1/R0 | 0.346 | 31 | 269 | 300 | 0.244 | 0.400 |
| C2/R0 | 0.243 | 24 | 276 | 300 | 0.240 | 0.246 |
| C4/R0 | 0.013 | 119 | 181 | 300 | 0.013 | 0.012 |
| C5/R0 | 0.056 | 102 | 198 | 300 | 0.112 | 0.039 |
| C6/R0 | 0.162 | 74 | 226 | 300 | 0.156 | 0.170 |
| C3/R1 | 0.027 | 87 | 213 | 300 | 0.069 | 0.007 |
| C3/R2 | 0.130 | 36 | 264 | 300 | 0.187 | 0.073 |
| C3/R3 | 0.075 | 53 | 247 | 300 | 0.084 | 0.068 |
| C0/R2 | 0.282 | 53 | 247 | 300 | 0.150 | 0.384 |

## Diagnostics

### 1. Rule effect: detection or compliance?

`C3/R2` adds the repeat-rule to the production prompt, which contains the history a repeat could be detected in. `C0/R2` adds the SAME rule to a prompt with NO history in it — nothing there to detect. If the two move U by similar amounts, the rule is being complied with, not applied. Read the loop-step columns first: R2 is a rule about repeats, so a median over all steps dilutes a real 4-step effect into noise.

| comparison | history in prompt | dU loop steps | up/n | dU all steps | up/n |
|---|---|---|---|---|---|
| C0/R2 - C0/R0 | **NO** | -0.027 | 26/78 | -0.024 | 78/300 |
| C3/R2 - C3/R0 | yes | 0.258 | 77/78 | 0.130 | 264/300 |

Decoy floor — `C3/R3` (an irrelevant rule, same shape and tone) vs baseline: median dU 0.075, 247 up / 53 down of 300. This is the pure *a rule was stated* effect; R1 and R2 have to beat it to mean anything.

### 2. Does the rule hit loop errors specifically?

A rule that raises U on every incorrect step equally is global pessimism, not rule application. Per stratum, on the production prompt.

| stratum | label | dU (C3/R2 - C3/R0) | up | down | n | dU (C3/R1 - C3/R0) |
|---|---|---|---|---|---|---|
| inadmissible | incorrect | 0.043 | 20 | 3 | 23 | 0.074 |
| loop | incorrect | 0.258 | 77 | 1 | 78 | 0.098 |
| other | incorrect | 0.111 | 43 | 6 | 49 | 0.025 |
| plain | correct | 0.044 | 82 | 23 | 105 | 0.002 |
| revisit | correct | 0.155 | 42 | 3 | 45 | 0.038 |

The `revisit` row is the false-positive test: those are CORRECT steps that legitimately repeat a location. If R2 raises U there too, the rule buys its separation by manufacturing false positives — weigh that against the Delta column before calling it an improvement.

### 3. Context ladder (factor A, no rule)

| context | contents | mean U inc | mean U cor | Delta |
|---|---|---|---|---|
| C0 | task + action | 0.736 | 0.725 | 0.010 |
| C1 | task + last observation + action | 0.790 | 0.640 | 0.150 |
| C2 | task + full history + action | 0.800 | 0.558 | 0.242 |
| C3 | task + full history + reasoning + action (production) | 0.491 | 0.243 | 0.248 |
| C4 | task + full history + reasoning, no action | 0.488 | 0.259 | 0.229 |
| C5 | production + the OUTCOME of the action (pre-hindsight) | 0.684 | 0.288 | 0.396 |
| C6 | production + outcome + the agent's next step (pre-hindsight, full) | 0.693 | 0.394 | 0.299 |

**C5/C6 are pre-hindsight**: they show the probe what the action actually produced. Expect them to separate best — that is the point, and it is not a fair comparison with C0-C4. They are a deployable probe only where actions are reversible (act, observe, assess, undo); otherwise read them as the ceiling on what P(True) could know. C6 minus C5 isolates how much of that comes from the agent's own continuation rather than the environment's response.

Caveat on this ladder: median step_idx is 20.0 (incorrect) vs 12.5 (correct). Where those differ, the incorrect steps carry longer histories, so C2/C3 vs C0/C1 partly measures history LENGTH, not history content.

At n~20, read the Steps section and the matrix CSV — the informative cases are individual steps where a condition flips the model hard, not the means.
