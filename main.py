import random


class Combat:
    def __init__(self, entity1, entity2):
        self.player = entity1
        self.enemy = entity2
        self.turn = 0 if random.random() <= 0.5 else 1
        self.combat_active = True
        self.winner = None
        self.player_won = False

    def action(self, action=None, direction=None, amount=None):
        if not self.combat_active:
            return False

        if self.turn == 0:
            active_entity = self.player
            target = self.enemy
        else:
            active_entity = self.enemy
            target = self.player

        if active_entity.health <= 0:
            self.combat_active = False
            self.winner = target
            self.player_won = target is self.player
            print(f"{active_entity.name} is already defeated.")
            return False

        previous_cd1 = active_entity.cd1
        previous_cd2 = active_entity.cd2
        active_entity.apply_effect()

        if active_entity.skipturn:
            print(f"{active_entity.name} is stunned and skips their turn.")
            active_entity.skipturn = False
            active_entity.update_cooldowns(previous_cd1, previous_cd2)
            active_entity.update_effects_after()
            self.turn = 1 - self.turn
            return True

        print(f"It is {active_entity.name}'s turn.")
        action_successful = active_entity.choice(target, action, direction, amount)

        if action_successful:
            active_entity.update_cooldowns(previous_cd1, previous_cd2)
            active_entity.update_effects_after()

            if target.health <= 0:
                self.combat_active = False
                self.winner = active_entity
                self.player_won = active_entity is self.player
                print(f"{target.name} has been defeated.")
                print(f"{active_entity.name} wins the combat.")
                return True

            self.turn = 1 - self.turn
            return True

        return False


class Combatant:
    def __init__(self, health, range, name):
        self.health = health
        self.range = range
        self.base_speed = 5
        self.base_success_chance = 1.0
        self.speed = self.base_speed
        self.damage_multi = 1.0
        self.pos = 10
        self.moves_in_a_row = 0
        self.success_chance = 1.0
        self.base_dodge_chance = 0.0
        self.dodge_chance = self.base_dodge_chance
        self.cd1 = 0
        self.cd2 = 0
        self.skipturn = False
        self.damage_taken_multi = 1.0
        self.effects = []
        self.name = name

    def update_cooldowns(self, previous_cd1, previous_cd2):
        if self.cd1 == previous_cd1:
            self.cd1 = max(0, self.cd1 - 1)

        if self.cd2 == previous_cd2:
            self.cd2 = max(0, self.cd2 - 1)

    def update_effects_after(self):
        self.effects = [
            (effect, duration - 1)
            for effect, duration in self.effects
            if duration > 1
        ]

    def apply_effect(self):
        self.speed = self.base_speed
        self.damage_multi = 1.0
        self.success_chance = self.base_success_chance
        self.dodge_chance = self.base_dodge_chance
        self.damage_taken_multi = 1.0

        for effect, duration in self.effects:
            if effect == "Chilled":
                self.speed = max(0, self.speed * 0.5)
            if effect == "Focused":
                self.success_chance = 1
                self.damage_multi = getattr(self, "focused_damage_multi", 1.5)
            if effect == "Acidic":
                self.damage_multi = 0.7
            if effect == "Protection":
                self.damage_taken_multi = 0.2
            if effect == "Stunned":
                self.skipturn = True
            if effect == "Dodge":
                self.dodge_chance = getattr(self, "knife_dance_dodge_chance", 0.3)

    def take_damage(self, amount, attacker=None):
        if attacker is None:
            hit_chance = 1.0 - self.dodge_chance
        else:
            hit_chance = max(0.0, attacker.success_chance - self.dodge_chance)

        if random.random() > hit_chance:
            return 0

        reduced = amount * self.damage_taken_multi
        self.health -= reduced
        self.damage_taken_multi = 1.0

        if any(effect == "Protection" for effect, _ in self.effects):
            self.effects = [(effect, duration) for effect, duration in self.effects if effect != "Protection"]

        return reduced

    def move(self, direction, amount):
        self.pos += direction * self.speed * amount
        self.moves_in_a_row += 1
        print(f"{self.name} moves to tile {self.pos}")
        return True


class Monster(Combatant):
    def __init__(self, health, damage, success_chance, range, speed, name):
        super().__init__(health, range, name)
        self.damage = damage
        self.success_chance = success_chance
        self.speed = speed
        self.base_speed = speed
        self.base_success_chance = success_chance
        self.pos = 30

    def attack(self, target):
        damage = self.damage * self.damage_multi
        dealt = target.take_damage(damage, self)
        if dealt > 0:
            print(f"{self.name}'s attack has hit you, dealing {dealt} damage. {target.name} has {target.health} health remaining.")
        else:
            print(f"{self.name}'s attack has missed you, dealing 0 damage. {target.name} has {target.health} health remaining.")

    def move(self, target):
        if target.pos > self.pos:
            direction = 1
        else:
            direction = -1

        if direction == 1:
            closest_pos = self.pos + self.speed
        else:
            closest_pos = self.pos - self.speed

        if closest_pos > 40:
            closest_pos = 40
        elif closest_pos < 0:
            closest_pos = 0

        new_pos = closest_pos

        if self.range > target.range:
            if direction == 1:
                attack_position = target.pos - self.range
                safe_position = target.pos - target.range - 1
            else:
                attack_position = target.pos + self.range
                safe_position = target.pos + target.range + 1

            if direction == 1:
                preferred_position = max(attack_position, safe_position)
                if closest_pos < preferred_position:
                    new_pos = closest_pos
                else:
                    new_pos = preferred_position
            else:
                preferred_position = min(attack_position, safe_position)
                if closest_pos > preferred_position:
                    new_pos = closest_pos
                else:
                    new_pos = preferred_position

            if new_pos > 40:
                new_pos = 40
            elif new_pos < 0:
                new_pos = 0

            if abs(target.pos - new_pos) > self.range:
                new_pos = closest_pos

        self.pos = new_pos
        print(f"{self.name} moves closer to {target.name}, now at tile {self.pos}")

    def choice(self, target, action=None, direction=None, amount=None):
        if abs(target.pos - self.pos) <= self.range:
            self.attack(target)
            self.moves_in_a_row = 0
            return True
        elif self.moves_in_a_row < 3:
            self.move(target)
            self.moves_in_a_row += 1
            return True
        else:
            print(f"{self.name} waits instead of moving.")
            self.moves_in_a_row = 0
            return True


class Wizard_Spellbook(Combatant):
    def __init__(self):
        super().__init__(50, 10, "Wizard Spellbook")

    def firebolt(self, target):
        if abs(target.pos - self.pos) > self.range:
            print(f"{self.name} cannot cast Firebolt: target is out of range.")
            return False

        if self.cd1 != 0:
            print(f"{self.name} cannot cast Firebolt yet. Cooldown: {self.cd1}")
            return False

        self.cd1 = 0
        damage = 10 * self.damage_multi
        dealt = target.take_damage(damage, self)
        print(f"{self.name} casts Firebolt on {target.name}, dealing {dealt} damage. {target.name} has {target.health} health remaining.")
        return True

    def wind_gust(self, target):
        if abs(target.pos - self.pos) > self.range:
            print(f"{self.name} cannot cast Wind Gust: target is out of range.")
            return False

        if self.cd2 != 0:
            print(f"{self.name} cannot cast Wind Gust yet. Cooldown: {self.cd2}")
            return False

        self.cd2 = 2
        damage = 12 * self.damage_multi
        dealt = target.take_damage(damage, self)
        if target.pos >= self.pos:
            target.pos = min(target.pos + 3, 40)
        else:
            target.pos = max(target.pos - 3, 0)
        print(f"{self.name} casts Wind Gust on {target.name}, dealing {dealt} damage. {target.name} has {target.health} health remaining. {target.name} was pushed back to tile {target.pos}")
        return True

    def move(self, direction, amount):
        return super().move(direction, amount)

    def choice(self, target, action=None, direction=None, amount=None):
        if action == "firebolt":
            return self.firebolt(target)
        if action == "wind_gust":
            return self.wind_gust(target)
        if action == "move":
            return self.move(direction, amount)
        return False


class Wizard_staff(Combatant):
    def __init__(self):
        super().__init__(75, 9, "Wizard Staff")

    def chill_touch(self, target):
        if abs(target.pos - self.pos) > self.range:
            print(f"{self.name} cannot cast Chill Touch: target is out of range.")
            return False

        if self.cd1 != 0:
            print(f"{self.name} cannot cast Chill Touch yet. Cooldown: {self.cd1}")
            return False

        self.cd1 = 1
        damage = 7 * self.damage_multi
        dealt = target.take_damage(damage, self)
        target.effects.append(("Chilled", 2))
        print(f"{self.name} casts Chill Touch on {target.name}, dealing {dealt} damage. {target.name} has {target.health} health remaining.")
        return True

    def acid_splash(self, target):
        if abs(target.pos - self.pos) > self.range:
            print(f"{self.name} cannot cast Acid Splash: target is out of range.")
            return False

        if self.cd2 != 0:
            print(f"{self.name} cannot cast Acid Splash yet. Cooldown: {self.cd2}")
            return False

        self.cd2 = 2
        damage = 14 * self.damage_multi
        dealt = target.take_damage(damage, self)
        target.effects.append(("Acidic", 2))
        print(f"{self.name} casts Acid Splash on {target.name}, dealing {dealt} damage and applying acidic. {target.name} has {target.health} health remaining.")
        return True

    def choice(self, target, action=None, direction=None, amount=None):
        if action == "chill_touch":
            return self.chill_touch(target)
        if action == "acid_splash":
            return self.acid_splash(target)
        if action == "move":
            return self.move(direction, amount)
        return False

class Barbarian_Battleaxe(Combatant):
    def __init__(self):
        super().__init__(225, 3, "Barbarian Battleaxe")

    def slice(self, target):
        if abs(target.pos - self.pos) > self.range:
            print(f"{self.name} cannot cast Slice: target is out of range.")
            return False

        if self.cd1 != 0:
            print(f"{self.name} cannot cast Slice yet. Cooldown: {self.cd1}")
            return False

        self.cd1 = 0
        damage = 5 * self.damage_multi
        dealt = target.take_damage(damage, self)
        print(f"{self.name} casts Slice on {target.name}, dealing {dealt} damage. {target.name} has {target.health} health remaining.")
        return True

    def whirlwind(self, target):
        if abs(target.pos - self.pos) > self.range:
            print(f"{self.name} cannot cast Whirlwind: target is out of range.")
            return False

        if self.cd2 != 0:
            print(f"{self.name} cannot cast Whirlwind yet. Cooldown: {self.cd2}")
            return False

        self.cd2 = 2
        first_damage = 16 * self.damage_multi
        dealt_first = target.take_damage(first_damage, self)
        print(f"{self.name} casts Whirlwind on {target.name}, dealing {dealt_first} damage. {target.name} has {target.health} health remaining.")

        if random.random() < 0.5:
            second_damage = 8 * self.damage_multi
            dealt_second = target.take_damage(second_damage, self)
            print(f"Whirlwind hits a second time, dealing {dealt_second} damage. {target.name} has {target.health} health remaining.")

        return True

    def choice(self, target, action=None, direction=None, amount=None):
        if action == "slice":
            return self.slice(target)
        if action == "whirlwind":
            return self.whirlwind(target)
        if action == "move":
            return self.move(direction, amount)
        return False

class Barbarian_Club(Combatant):
    def __init__(self):
        super().__init__(200, 4, "Barbarian Club")

    def clobber(self, target):
        if abs(target.pos - self.pos) > self.range:
            print(f"{self.name} cannot cast Clobber: target is out of range.")
            return False

        if self.cd1 != 0:
            print(f"{self.name} cannot cast Clobber yet. Cooldown: {self.cd1}")
            return False

        self.cd1 = 0
        damage = 6 * self.damage_multi
        dealt = target.take_damage(damage, self)
        print(f"{self.name} casts Clobber on {target.name}, dealing {dealt} damage. {target.name} has {target.health} health remaining.")
        return True

    def smash(self, target):
        if abs(target.pos - self.pos) > self.range:
            print(f"{self.name} cannot cast Smash: target is out of range.")
            return False

        if self.cd2 != 0:
            print(f"{self.name} cannot cast Smash yet. Cooldown: {self.cd2}")
            return False

        self.cd2 = 2
        damage = 14 * self.damage_multi
        dealt = target.take_damage(damage, self)
        if dealt > 0 and random.random() < 0.4:
            target.effects.append(("Stunned", 1))
            print(f"{self.name} uses Smash on {target.name}, dealing {dealt} damage and stunning {target.name} for 1 round. {target.name} has {target.health} health remaining.")
        else:
            print(f"{self.name} casts Smash on {target.name}, dealing {dealt} damage. {target.name} has {target.health} health remaining.")
        return True

    def choice(self, target, action=None, direction=None, amount=None):
        if action == "clobber":
            return self.clobber(target)
        if action == "smash":
            return self.smash(target)
        if action == "move":
            return self.move(direction, amount)
        return False

class Paladin_Greatsword(Combatant):
    def __init__(self):
        super().__init__(150, 5, "Paladin Greatsword")

    def cleave(self, target):
        if abs(target.pos - self.pos) > self.range:
            print(f"{self.name} cannot cast Cleave: target is out of range.")
            return False

        if self.cd1 != 0:
            print(f"{self.name} cannot cast Cleave yet. Cooldown: {self.cd1}")
            return False

        self.cd1 = 0
        if random.random() < 0.25:
            damage = 4 * self.damage_multi
            dealt = target.take_damage(damage, self)
            print(f"{self.name} strikes at a bad angle with Cleave, dealing {dealt} damage. {target.name} has {target.health} health remaining.")
        else:
            damage = 8 * self.damage_multi
            dealt = target.take_damage(damage, self)
            print(f"{self.name} casts Cleave on {target.name}, dealing {dealt} damage. {target.name} has {target.health} health remaining.")
        return True

    def decapitate(self, target):
        if abs(target.pos - self.pos) > self.range:
            print(f"{self.name} cannot cast Decapitate: target is out of range.")
            return False

        if self.cd2 != 0:
            print(f"{self.name} cannot cast Decapitate yet. Cooldown: {self.cd2}")
            return False

        self.cd2 = 4
        damage = target.health
        dealt = target.take_damage(damage, self)
        print(f"{self.name} casts Decapitate on {target.name}, dealing {dealt} damage and instakilling them. {target.name} has {target.health} health remaining.")
        return True

    def choice(self, target, action=None, direction=None, amount=None):
        if action == "cleave":
            return self.cleave(target)
        if action == "decapitate":
            return self.decapitate(target)
        if action == "move":
            return self.move(direction, amount)
        return False


class Paladin_Sword_and_Shield(Combatant):
    def __init__(self):
        super().__init__(175, 6, "Paladin Sword and Shield")

    def block(self):
        self.effects.append(("Protection", 1))
        self.damage_taken_multi = 0.2
        print(f"{self.name} casts Block, taking 80% less damage from the next attack.")
        return True

    def shield_bash(self, target):
        if abs(target.pos - self.pos) > self.range:
            print(f"{self.name} cannot cast Shield Bash: target is out of range.")
            return False

        if self.cd2 != 0:
            print(f"{self.name} cannot cast Shield Bash yet. Cooldown: {self.cd2}")
            return False

        self.cd2 = 2
        damage = 12 * self.damage_multi
        dealt = target.take_damage(damage, self)
        print(f"{self.name} casts Shield Bash on {target.name}, dealing {dealt} damage. {target.name} has {target.health} health remaining.")

        if dealt > 0 and random.random() < 0.15:
            target.effects.append(("Stunned", 1))
            print(f"{target.name} is stunned for 1 turn.")

        return True

    def choice(self, target, action=None, direction=None, amount=None):
        if action == "block":
            return self.block()
        if action == "shield_bash":
            return self.shield_bash(target)
        if action == "move":
            return self.move(direction, amount)
        return False


class Rogue_Two_Daggers(Combatant):
    def __init__(self):
        super().__init__(100, 7, "Rogue Two Daggers")
        self.throwing_knives_success_chance = 0.7
        self.throwing_knives_damage = 4
        self.focused_damage_multi = 1.5
        self.knife_dance_dodge_chance = 0.3
        self.knife_dance_dodge_rounds = 3
        self.base_success_chance = self.throwing_knives_success_chance
        self.success_chance = self.base_success_chance

    def throwing_knives(self, target):
        if abs(target.pos - self.pos) > self.range:
            print(f"{self.name} cannot use Throwing Knives: target is out of range.")
            return False

        damage = self.throwing_knives_damage * self.damage_multi
        dealt = target.take_damage(damage, self)
        if dealt > 0:
            print(f"{self.name} throws knives at {target.name}, dealing {dealt} damage. {target.name} has {target.health} health remaining.")
        else:
            print(f"{self.name}'s Throwing Knives missed {target.name}.")
        return True

    def knife_dance(self):
        self.effects.append(("Focused", 2))
        self.effects.append(("Dodge", self.knife_dance_dodge_rounds + 1))
        print(f"{self.name} performs Knife Dance. The next attack deals 1.5x damage with 100% accuracy, and dodge chance increases by 30% for the next 3 rounds.")
        return True

    def choice(self, target, action=None, direction=None, amount=None):
        if action == "throwing_knives":
            return self.throwing_knives(target)
        if action == "knife_dance":
            return self.knife_dance()
        if action == "move":
            return self.move(direction, amount)
        return False


class Rogue_Crossbow(Combatant):
    def __init__(self):
        super().__init__(125, 8, "Rogue Crossbow")

    def single_bolt(self, target):
        if abs(target.pos - self.pos) > self.range:
            print(f"{self.name} cannot use Single Bolt: target is out of range.")
            return False

        if self.cd1 != 0:
            print(f"{self.name} cannot use Single Bolt yet. Cooldown: {self.cd1}")
            return False

        self.cd1 = 1
        damage = 5 * self.damage_multi
        dealt = target.take_damage(damage, self)
        print(f"{self.name} fires a single bolt at {target.name}, dealing {dealt} damage. {target.name} has {target.health} health remaining.")
        return True

    def triple_bolt(self, target):
        if abs(target.pos - self.pos) > self.range:
            print(f"{self.name} cannot use Triple Bolt: target is out of range.")
            return False

        if self.cd2 != 0:
            print(f"{self.name} cannot use Triple Bolt yet. Cooldown: {self.cd2}")
            return False

        self.cd2 = 2
        damage = 15 * self.damage_multi
        dealt = target.take_damage(damage, self)
        if dealt > 0 and random.random() < 0.45:
            target.effects.append(("Stunned", 1))
        print(f"{self.name} fires three bolts at {target.name}, dealing {dealt} damage. {target.name} has {target.health} health remaining.")
        return True

    def choice(self, target, action=None, direction=None, amount=None):
        if action == "single_bolt":
            return self.single_bolt(target)
        if action == "triple_bolt":
            return self.triple_bolt(target)
        if action == "move":
            return self.move(direction, amount)
        return False

    
