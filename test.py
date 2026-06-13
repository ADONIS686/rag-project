def func(nums, target):
    for i in range(len(nums)):
        a = nums[i];
        for j in range(i+1, len(nums)):
            b = nums[j];
            if a + b == target:
                return [i, j]


nums = [2,7,11,15]
target = 9
i, j = func(nums, target)
print(f"Indices: [{i}, {j}]")
print(f"因为 nums[{i}] + nums[{j}] = {nums[i]} + {nums[j]} = {target}")