
def load_dataset(data_name):
    dataset = {'train':[], 'test':[], 'valid':[]}
    for key in dataset:
        try:
            with open("resources/data/%s-%s.txt"%(data_name, key),'r') as infile:
                for episode_idx, line in enumerate(infile):
                    data_item = eval(line.strip('\n'))
                    data_item['episode_idx'] = episode_idx
                    dataset[key].append(data_item)
        except FileNotFoundError:
            continue
    return dataset