import simpy
from random import random, seed, randint


def idle(env):
  while True:
      try:
          print('idle at %s' % env.now)
          yield env.timeout(1)
      except simpy.Interrupt as i:
          print('idle interrupted at %s: %s' % (env.now, i.cause))
          break

def charging(env):
  while True:
      try:
          print('Charging at %s' % env.now)
          yield env.timeout(1)
      except simpy.Interrupt as i:
          print('Charging interrupted at %s: %s' % (env.now, i.cause))
          break


def drive(env):
    print('start driving at %s' % env.now)
    yield env.timeout(5)
    print('finish driving at %s' % env.now)


def live(env):
    while True:
        if (random() <= 0.5):
            state = env.process(idle(env))
        else:
            state = env.process(charging(env))

        # Wait for customer
        yield env.timeout(randint(5,10))
        if not state.triggered:
            state.interrupt('Customer arrived')

        yield env.process(drive(env))





env = simpy.Environment()
env.process(live(env))


env.run(100)
