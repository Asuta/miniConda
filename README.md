# Mini Conda 本地环境项目

这是一个使用 mini conda 创建的本地环境项目。

## 环境设置

### 创建环境（这个不对）

```bash
conda env create -f environment.yml
```

### 激活环境（这个不对）

```bash
conda activate miniConda
```

# 使用指定路径创建环境（这个对）

conda env create -f environment.yml -p ./env

# 激活环境（这个对）

conda activate ./env

### 停用环境

```bash
conda deactivate
```

### 删除环境

```bash
conda env remove -n miniConda
```

## 项目结构

```
miniConda/
├── environment.yml     # conda 环境配置文件
├── README.md          # 项目说明文档
├── src/               # 源代码目录
├── data/              # 数据文件目录
├── notebooks/         # Jupyter notebook 目录
├── tests/             # 测试文件目录
└── requirements.txt   # pip 依赖文件（备用）
```

## 使用说明

1. 首先确保已安装 miniconda 或 anaconda
2. 在项目根目录运行 `conda env create -f environment.yml` 创建环境
3. 使用 `conda activate miniConda` 激活环境
4. 开始您的项目开发

## 环境管理

- 添加新包：`conda install package_name` 或 `pip install package_name`
- 更新环境文件：`conda env export > environment.yml`
- 查看已安装包：`conda list`
