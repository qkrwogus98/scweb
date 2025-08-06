import colorsys
import random


class UniqueRGBGenerator:
    def __init__(self):
        self.used_colors = set()
        self.grids = [(r, g, b) for r in range(0, 256, 10)
                                for g in range(0, 256, 10)
                                for b in range(0, 256, 10)]

    def generate(self):
        if not self.grids:  # 모든 그리드가 사용되면
            return None

        base_r, base_g, base_b = random.choice(self.grids)
        self.grids.remove((base_r, base_g, base_b))

        r = random.randint(base_r, min(255, base_r + 9))
        g = random.randint(base_g, min(255, base_g + 9))
        b = random.randint(base_b, min(255, base_b + 9))

        while (r, g, b) in self.used_colors:
            r = random.randint(base_r, min(255, base_r + 9))
            g = random.randint(base_g, min(255, base_g + 9))
            b = random.randint(base_b, min(255, base_b + 9))

        self.used_colors.add((r, g, b))
        return r, g, b


class DistinctColorGenerator:
    def __init__(self, total_colors=100):
        self.hue_step = 1.0 / total_colors
        self.current_step = 0

    def generate(self):
        if self.current_step >= 1:
            return None

        hue = self.current_step
        saturation = random.uniform(0.7, 1.0)  # 보통 0.7~1.0 범위의 saturation 값이 뚜렷한 색상을 만듭니다.
        lightness = random.uniform(0.4, 0.6)  # 너무 밝거나 너무 어두운 색상을 피하기 위해 0.4~0.6 범위의 lightness를 선택합니다.

        self.current_step += self.hue_step

        r, g, b = [int(x * 255) for x in colorsys.hls_to_rgb(hue, lightness, saturation)]
        return r, g, b


if __name__ == "__main__":
    generator = DistinctColorGenerator(total_colors=10)
    for _ in range(10):
        print(generator.generate())

    # generator = UniqueRGBGenerator()
    # for _ in range(10):
    #     print(generator.generate())
