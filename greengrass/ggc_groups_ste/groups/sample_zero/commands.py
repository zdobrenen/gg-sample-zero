import fire

from ggc_custom_sdk.groups import GroupCommands
from ggc_custom_sdk.utils import gen_group_path


class SampleZeroGroupCommands(GroupCommands):

    GROUP_PATH = gen_group_path(__file__)


    def __init__(self):
        super(SampleZeroGroupCommands, self).__init__()



def main():
    fire.Fire(SampleZeroGroupCommands())


if __name__ == '__main__':
    main()
