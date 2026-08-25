# 🎨 Artificial-It

<div align="center">

**AI-Powered Image Generation Application with Stable Diffusion**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9%2B-green.svg)](https://www.python.org/)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.5%2B-orange.svg)](https://www.riverbankcomputing.com/software/pyqt/)
[![Hugging Face](https://img.shields.io/badge/Hugging%20Face-supported-yellow.svg)](https://huggingface.co)

**Generate stunning AI images from text prompts with an intuitive desktop application.**

</div>

---

## 🌟 Features

- **🚀 Lightning-Fast Generation**: Powered by Stable Diffusion and PyTorch
- **🎯 Live Preview**: Real-time image preview during generation process
- **⚡ Non-Blocking UI**: Async operations keep your interface responsive
- **🖼️ Multiple Model Support**: Works with various diffusion models (SD1.5, SDXL, etc.)
- **🎨 Professional Controls**: Fine-tune parameters like guidance scale, steps, resolution
- **💾 Efficient Storage**: Smart temp directory management for large files
- **🔒 Privacy-Focused**: All processing happens locally on your machine

---

## 📸 Screenshots

*Note: Add actual screenshots of your application here once you have them.*

<div align="center">

```markdown
<!-- Replace with actual screenshots -->
[Application Main Window Screenshot]
```

</div>

---

## 🛠️ Installation

### Prerequisites

- **Python 3.9 or higher** ([Download](https://www.python.org/downloads/))
- **GPU with CUDA support** (NVIDIA recommended for fastest generation)
- **8GB+ RAM minimum** (16GB+ recommended for best performance)

### Quick Install

```bash
# Clone the repository
git clone https://github.com/RobertSullender/Artificial-It.git
cd Artificial-It

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

### Manual Install

If you prefer installing dependencies individually:

```bash
pip install PyQt6>=6.5.0 torch>=2.0.0 diffusers>=0.31.0 pillow scipy numpy
```

---

## 🎯 Usage

### Basic Image Generation

1. Launch the application:
   ```bash
   python src/main.py
   ```

2. Enter your text prompt in the input field

3. Select your desired model from the dropdown menu

4. Click **"Generate"** button

5. Watch the live preview update as your image is created!

### Advanced Configuration

You can fine-tune generation parameters:

- **Resolution**: Adjust width and height (default: 512×512)
- **Steps**: Number of diffusion steps (more = better quality, slower)
- **Guidance Scale**: How closely to follow your prompt (7-12 recommended)
- **Seed**: Reproducible results (random or custom value)

---

## 📋 Model Download Notice

### Important: AI Models Are Not Included

This application does **NOT** include AI models in the repository. Models are downloaded automatically at runtime from Hugging Face and other sources.

**You are responsible for:**
- Reviewing each model's license terms before use
- Ensuring your usage complies with model restrictions
- Understanding that different models may have different permitted uses

### Example Model Licenses

| Model | License | Documentation |
|-------|---------|---------------|
| Stable Diffusion SD1.5 | CreativeML Open RAIL-M | [Stability AI](https://stability.ai/text-to-image-models-license) |

For complete information, see the [`LICENSE`](./LICENSE) file for model download policies.

---

## 🧪 Known Limitations

### Sampler Parameter (Current Version)
- **Status**: Documented limitation
- **Description**: In Diffusers v0.31+, sampler selection is determined at pipeline creation time
- **Impact**: Changing sampler dropdown may not affect output in current version
- **Workaround**: Coming in next release with updated Diffusers integration

### GPU Memory Requirements
- **Minimum**: 4GB VRAM for SD1.5 (float16)
- **Recommended**: 8GB+ VRAM for better performance and larger models
- **Low VRAM**: Models may be offloaded to CPU if insufficient GPU memory available

---

## 🤝 Contributing

We welcome contributions! See our [Contributing Guidelines](docs/CONTRIBUTING.md) for details on:

- Reporting bugs
- Suggesting features
- Submitting pull requests
- Code style guidelines
- Development setup

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

**Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before contributing.**

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [`docs/README.md`](./docs/README.md) | Project overview and summary |
| [`src/docs/ARCHITECTURE.md`](./src/docs/ARCHITECTURE.md) | Technical architecture and design patterns |
| [`CHANGELOG.md`](./CHANGELOG.md) | Version history and release notes |

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

### Third-Party Dependencies

See [`NOTICE.txt`](./NOTICE.txt) for a complete list of third-party components and their licenses.

---

## 🔒 Security

Security vulnerabilities can be reported through GitHub Issues (marked appropriately) or directly via our [Security Policy](SECURITY.md).

We take the security of this project seriously and appreciate responsible disclosure from the community.

---

## 🙏 Acknowledgments

- **[Stability AI](https://stability.ai)** for Stable Diffusion models
- **[Hugging Face](https://huggingface.co)** for transformers and diffusers libraries
- **[PyTorch Team](https://pytorch.org/)** for the deep learning framework
- **[Qt Company](https://www.qt.io/)** for PyQt6 GUI framework

---

## 📞 Support & Contact

- **GitHub Issues**: [Report bugs and request features](https://github.com/RobertSullender/Artificial-It/issues)
- **Documentation**: See the [docs/](./docs/) directory for technical details

---

<div align="center">

**Built with ❤️ using Stable Diffusion, PyTorch, and PyQt6**

*Last Updated: 2024*

</div>