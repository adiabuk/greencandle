#!/usr/bin/env python

def get_sequences(li):
    current_li = []
    sequences = []
    for index, item in enumerate(li):
        print(index, item)
        if index == 0:
            current_li.append((index, item))
            continue

        if item >= li[index -1]:
            print("still in seq", current_li, "item:", item)
            current_li.append((index, item))
            if index == len(li) - 1 and len(current_li) > 1:
                sequences .append(current_li)
        elif item < li[index -1]:
            print("end of seq")
            sequences.append(current_li)
            current_li =  [(index, item)]

    print(sequences, len(sequences))
    for sequence in sequences:
        start = sequence[0][-1]
        end = sequence[-1][-1]
        diff = end-start
        loc = (sequence[0][0], sequence[-1][0])
        print("start:", start, "end:", end, "diff:", diff, "loc:", loc)

if __name__ == "__main__":

    get_sequences([1, 2, 9, 8, 9, 10, 11, 12])
