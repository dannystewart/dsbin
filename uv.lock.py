version = 1
requires-python = ">=3.11, <3.13"

[[package]]
name = "aiohappyeyeballs"
version = "2.4.3"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/bc/69/2f6d5a019bd02e920a3417689a89887b39ad1e350b562f9955693d900c40/aiohappyeyeballs-2.4.3.tar.gz", hash = "sha256:75cf88a15106a5002a8eb1dab212525c00d1f4c0fa96e551c9fbe6f09a621586", size = 21809 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/f7/d8/120cd0fe3e8530df0539e71ba9683eade12cae103dd7543e50d15f737917/aiohappyeyeballs-2.4.3-py3-none-any.whl", hash = "sha256:8a7a83727b2756f394ab2895ea0765a0a8c475e3c71e98d43d76f22b4b435572", size = 14742 },
]

[[package]]
name = "aiohttp"
version = "3.10.10"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "aiohappyeyeballs" },
    { name = "aiosignal" },
    { name = "attrs" },
    { name = "frozenlist" },
    { name = "multidict" },
    { name = "yarl" },
]
sdist = { url = "https://files.pythonhosted.org/packages/17/7e/16e57e6cf20eb62481a2f9ce8674328407187950ccc602ad07c685279141/aiohttp-3.10.10.tar.gz", hash = "sha256:0631dd7c9f0822cc61c88586ca76d5b5ada26538097d0f1df510b082bad3411a", size = 7542993 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/72/31/3c351d17596194e5a38ef169a4da76458952b2497b4b54645b9d483cbbb0/aiohttp-3.10.10-cp311-cp311-macosx_10_9_universal2.whl", hash = "sha256:c30a0eafc89d28e7f959281b58198a9fa5e99405f716c0289b7892ca345fe45f", size = 586501 },
    { url = "https://files.pythonhosted.org/packages/a4/a8/a559d09eb08478cdead6b7ce05b0c4a133ba27fcdfa91e05d2e62867300d/aiohttp-3.10.10-cp311-cp311-macosx_10_9_x86_64.whl", hash = "sha256:258c5dd01afc10015866114e210fb7365f0d02d9d059c3c3415382ab633fcbcb", size = 398993 },
    { url = "https://files.pythonhosted.org/packages/c5/47/7736d4174613feef61d25332c3bd1a4f8ff5591fbd7331988238a7299485/aiohttp-3.10.10-cp311-cp311-macosx_11_0_arm64.whl", hash = "sha256:15ecd889a709b0080f02721255b3f80bb261c2293d3c748151274dfea93ac871", size = 390647 },
    { url = "https://files.pythonhosted.org/packages/27/21/e9ba192a04b7160f5a8952c98a1de7cf8072ad150fa3abd454ead1ab1d7f/aiohttp-3.10.10-cp311-cp311-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:f3935f82f6f4a3820270842e90456ebad3af15810cf65932bd24da4463bc0a4c", size = 1306481 },
    { url = "https://files.pythonhosted.org/packages/cf/50/f364c01c8d0def1dc34747b2470969e216f5a37c7ece00fe558810f37013/aiohttp-3.10.10-cp311-cp311-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:413251f6fcf552a33c981c4709a6bba37b12710982fec8e558ae944bfb2abd38", size = 1344652 },
    { url = "https://files.pythonhosted.org/packages/1d/c2/74f608e984e9b585649e2e83883facad6fa3fc1d021de87b20cc67e8e5ae/aiohttp-3.10.10-cp311-cp311-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:d1720b4f14c78a3089562b8875b53e36b51c97c51adc53325a69b79b4b48ebcb", size = 1378498 },
    { url = "https://files.pythonhosted.org/packages/9f/a7/05a48c7c0a7a80a5591b1203bf1b64ca2ed6a2050af918d09c05852dc42b/aiohttp-3.10.10-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:679abe5d3858b33c2cf74faec299fda60ea9de62916e8b67e625d65bf069a3b7", size = 1292718 },
    { url = "https://files.pythonhosted.org/packages/7d/78/a925655018747e9790350180330032e27d6e0d7ed30bde545fae42f8c49c/aiohttp-3.10.10-cp311-cp311-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:79019094f87c9fb44f8d769e41dbb664d6e8fcfd62f665ccce36762deaa0e911", size = 1251776 },
    { url = "https://files.pythonhosted.org/packages/47/9d/85c6b69f702351d1236594745a4fdc042fc43f494c247a98dac17e004026/aiohttp-3.10.10-cp311-cp311-musllinux_1_2_aarch64.whl", hash = "sha256:fe2fb38c2ed905a2582948e2de560675e9dfbee94c6d5ccdb1301c6d0a5bf092", size = 1271716 },
    { url = "https://files.pythonhosted.org/packages/7f/a7/55fc805ff9b14af818903882ece08e2235b12b73b867b521b92994c52b14/aiohttp-3.10.10-cp311-cp311-musllinux_1_2_i686.whl", hash = "sha256:a3f00003de6eba42d6e94fabb4125600d6e484846dbf90ea8e48a800430cc142", size = 1266263 },
    { url = "https://files.pythonhosted.org/packages/1f/ec/d2be2ca7b063e4f91519d550dbc9c1cb43040174a322470deed90b3d3333/aiohttp-3.10.10-cp311-cp311-musllinux_1_2_ppc64le.whl", hash = "sha256:1bbb122c557a16fafc10354b9d99ebf2f2808a660d78202f10ba9d50786384b9", size = 1321617 },
    { url = "https://files.pythonhosted.org/packages/c9/a3/b29f7920e1cd0a9a68a45dd3eb16140074d2efb1518d2e1f3e140357dc37/aiohttp-3.10.10-cp311-cp311-musllinux_1_2_s390x.whl", hash = "sha256:30ca7c3b94708a9d7ae76ff281b2f47d8eaf2579cd05971b5dc681db8caac6e1", size = 1339227 },
    { url = "https://files.pythonhosted.org/packages/8a/81/34b67235c47e232d807b4bbc42ba9b927c7ce9476872372fddcfd1e41b3d/aiohttp-3.10.10-cp311-cp311-musllinux_1_2_x86_64.whl", hash = "sha256:df9270660711670e68803107d55c2b5949c2e0f2e4896da176e1ecfc068b974a", size = 1299068 },
    { url = "https://files.pythonhosted.org/packages/04/1f/26a7fe11b6ad3184f214733428353c89ae9fe3e4f605a657f5245c5e720c/aiohttp-3.10.10-cp311-cp311-win32.whl", hash = "sha256:aafc8ee9b742ce75044ae9a4d3e60e3d918d15a4c2e08a6c3c3e38fa59b92d94", size = 362223 },
    { url = "https://files.pythonhosted.org/packages/10/91/85dcd93f64011434359ce2666bece981f08d31bc49df33261e625b28595d/aiohttp-3.10.10-cp311-cp311-win_amd64.whl", hash = "sha256:362f641f9071e5f3ee6f8e7d37d5ed0d95aae656adf4ef578313ee585b585959", size = 381576 },
    { url = "https://files.pythonhosted.org/packages/ae/99/4c5aefe5ad06a1baf206aed6598c7cdcbc7c044c46801cd0d1ecb758cae3/aiohttp-3.10.10-cp312-cp312-macosx_10_9_universal2.whl", hash = "sha256:9294bbb581f92770e6ed5c19559e1e99255e4ca604a22c5c6397b2f9dd3ee42c", size = 583536 },
    { url = "https://files.pythonhosted.org/packages/a9/36/8b3bc49b49cb6d2da40ee61ff15dbcc44fd345a3e6ab5bb20844df929821/aiohttp-3.10.10-cp312-cp312-macosx_10_9_x86_64.whl", hash = "sha256:a8fa23fe62c436ccf23ff930149c047f060c7126eae3ccea005f0483f27b2e28", size = 395693 },
    { url = "https://files.pythonhosted.org/packages/e1/77/0aa8660dcf11fa65d61712dbb458c4989de220a844bd69778dff25f2d50b/aiohttp-3.10.10-cp312-cp312-macosx_11_0_arm64.whl", hash = "sha256:5c6a5b8c7926ba5d8545c7dd22961a107526562da31a7a32fa2456baf040939f", size = 390898 },
    { url = "https://files.pythonhosted.org/packages/38/d2/b833d95deb48c75db85bf6646de0a697e7fb5d87bd27cbade4f9746b48b1/aiohttp-3.10.10-cp312-cp312-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:007ec22fbc573e5eb2fb7dec4198ef8f6bf2fe4ce20020798b2eb5d0abda6138", size = 1312060 },
    { url = "https://files.pythonhosted.org/packages/aa/5f/29fd5113165a0893de8efedf9b4737e0ba92dfcd791415a528f947d10299/aiohttp-3.10.10-cp312-cp312-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:9627cc1a10c8c409b5822a92d57a77f383b554463d1884008e051c32ab1b3742", size = 1350553 },
    { url = "https://files.pythonhosted.org/packages/ad/cc/f835f74b7d344428469200105236d44606cfa448be1e7c95ca52880d9bac/aiohttp-3.10.10-cp312-cp312-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:50edbcad60d8f0e3eccc68da67f37268b5144ecc34d59f27a02f9611c1d4eec7", size = 1392646 },
    { url = "https://files.pythonhosted.org/packages/bf/fe/1332409d845ca601893bbf2d76935e0b93d41686e5f333841c7d7a4a770d/aiohttp-3.10.10-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:a45d85cf20b5e0d0aa5a8dca27cce8eddef3292bc29d72dcad1641f4ed50aa16", size = 1306310 },
    { url = "https://files.pythonhosted.org/packages/e4/a1/25a7633a5a513278a9892e333501e2e69c83e50be4b57a62285fb7a008c3/aiohttp-3.10.10-cp312-cp312-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:0b00807e2605f16e1e198f33a53ce3c4523114059b0c09c337209ae55e3823a8", size = 1260255 },
    { url = "https://files.pythonhosted.org/packages/f2/39/30eafe89e0e2a06c25e4762844c8214c0c0cd0fd9ffc3471694a7986f421/aiohttp-3.10.10-cp312-cp312-musllinux_1_2_aarch64.whl", hash = "sha256:f2d4324a98062be0525d16f768a03e0bbb3b9fe301ceee99611dc9a7953124e6", size = 1271141 },
    { url = "https://files.pythonhosted.org/packages/5b/fc/33125df728b48391ef1fcb512dfb02072158cc10d041414fb79803463020/aiohttp-3.10.10-cp312-cp312-musllinux_1_2_i686.whl", hash = "sha256:438cd072f75bb6612f2aca29f8bd7cdf6e35e8f160bc312e49fbecab77c99e3a", size = 1280244 },
    { url = "https://files.pythonhosted.org/packages/3b/61/e42bf2c2934b5caa4e2ec0b5e5fd86989adb022b5ee60c2572a9d77cf6fe/aiohttp-3.10.10-cp312-cp312-musllinux_1_2_ppc64le.whl", hash = "sha256:baa42524a82f75303f714108fea528ccacf0386af429b69fff141ffef1c534f9", size = 1316805 },
    { url = "https://files.pythonhosted.org/packages/18/32/f52a5e2ae9ad3bba10e026a63a7a23abfa37c7d97aeeb9004eaa98df3ce3/aiohttp-3.10.10-cp312-cp312-musllinux_1_2_s390x.whl", hash = "sha256:a7d8d14fe962153fc681f6366bdec33d4356f98a3e3567782aac1b6e0e40109a", size = 1343930 },
    { url = "https://files.pythonhosted.org/packages/05/be/6a403b464dcab3631fe8e27b0f1d906d9e45c5e92aca97ee007e5a895560/aiohttp-3.10.10-cp312-cp312-musllinux_1_2_x86_64.whl", hash = "sha256:c1277cd707c465cd09572a774559a3cc7c7a28802eb3a2a9472588f062097205", size = 1306186 },
    { url = "https://files.pythonhosted.org/packages/8e/fd/bb50fe781068a736a02bf5c7ad5f3ab53e39f1d1e63110da6d30f7605edc/aiohttp-3.10.10-cp312-cp312-win32.whl", hash = "sha256:59bb3c54aa420521dc4ce3cc2c3fe2ad82adf7b09403fa1f48ae45c0cbde6628", size = 359289 },
    { url = "https://files.pythonhosted.org/packages/70/9e/5add7e240f77ef67c275c82cc1d08afbca57b77593118c1f6e920ae8ad3f/aiohttp-3.10.10-cp312-cp312-win_amd64.whl", hash = "sha256:0e1b370d8007c4ae31ee6db7f9a2fe801a42b146cec80a86766e7ad5c4a259cf", size = 379313 },
]

[[package]]
name = "aiosignal"
version = "1.3.1"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "frozenlist" },
]
sdist = { url = "https://files.pythonhosted.org/packages/ae/67/0952ed97a9793b4958e5736f6d2b346b414a2cd63e82d05940032f45b32f/aiosignal-1.3.1.tar.gz", hash = "sha256:54cd96e15e1649b75d6c87526a6ff0b6c1b0dd3459f43d9ca11d48c339b68cfc", size = 19422 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/76/ac/a7305707cb852b7e16ff80eaf5692309bde30e2b1100a1fcacdc8f731d97/aiosignal-1.3.1-py3-none-any.whl", hash = "sha256:f8376fb07dd1e86a584e4fcdec80b36b7f81aac666ebc724e2c090300dd83b17", size = 7617 },
]

[[package]]
name = "ansicon"
version = "1.89.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/b6/e2/1c866404ddbd280efedff4a9f15abfe943cb83cde6e895022370f3a61f85/ansicon-1.89.0.tar.gz", hash = "sha256:e4d039def5768a47e4afec8e89e83ec3ae5a26bf00ad851f914d1240b444d2b1", size = 67312 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/75/f9/f1c10e223c7b56a38109a3f2eb4e7fe9a757ea3ed3a166754fb30f65e466/ansicon-1.89.0-py2.py3-none-any.whl", hash = "sha256:f1def52d17f65c2c9682cf8370c03f541f410c1752d6a14029f97318e4b9dfec", size = 63675 },
]

[[package]]
name = "argparse"
version = "1.4.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/18/dd/e617cfc3f6210ae183374cd9f6a26b20514bbb5a792af97949c5aacddf0f/argparse-1.4.0.tar.gz", hash = "sha256:62b089a55be1d8949cd2bc7e0df0bddb9e028faefc8c32038cc84862aefdd6e4", size = 70508 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/f2/94/3af39d34be01a24a6e65433d19e107099374224905f1e0cc6bbe1fd22a2f/argparse-1.4.0-py2.py3-none-any.whl", hash = "sha256:c31647edb69fd3d465a847ea3157d37bed1f95f19760b11a47aa91c04b666314", size = 23000 },
]

[[package]]
name = "attrs"
version = "24.2.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/fc/0f/aafca9af9315aee06a89ffde799a10a582fe8de76c563ee80bbcdc08b3fb/attrs-24.2.0.tar.gz", hash = "sha256:5cfb1b9148b5b086569baec03f20d7b6bf3bcacc9a42bebf87ffaaca362f6346", size = 792678 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/6a/21/5b6702a7f963e95456c0de2d495f67bf5fd62840ac655dc451586d23d39a/attrs-24.2.0-py3-none-any.whl", hash = "sha256:81921eb96de3191c8258c199618104dd27ac608d9366f5e35d011eae1867ede2", size = 63001 },
]

[[package]]
name = "azure-core"
version = "1.31.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "requests" },
    { name = "six" },
    { name = "typing-extensions" },
]
sdist = { url = "https://files.pythonhosted.org/packages/03/7a/f79ad135a276a37e61168495697c14ba1721a52c3eab4dae2941929c79f8/azure_core-1.31.0.tar.gz", hash = "sha256:656a0dd61e1869b1506b7c6a3b31d62f15984b1a573d6326f6aa2f3e4123284b", size = 277147 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/01/8e/fcb6a77d3029d2a7356f38dbc77cf7daa113b81ddab76b5593d23321e44c/azure_core-1.31.0-py3-none-any.whl", hash = "sha256:22954de3777e0250029360ef31d80448ef1be13b80a459bff80ba7073379e2cd", size = 197399 },
]

[[package]]
name = "azure-storage-blob"
version = "12.23.1"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "azure-core" },
    { name = "cryptography" },
    { name = "isodate" },
    { name = "typing-extensions" },
]
sdist = { url = "https://files.pythonhosted.org/packages/66/b2/df9ac2ea294e558fa8b6cdade9a14a938b07529f5194303664152819277a/azure_storage_blob-12.23.1.tar.gz", hash = "sha256:a587e54d4e39d2a27bd75109db164ffa2058fe194061e5446c5a89bca918272f", size = 566114 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/df/bf/f19dd2261dd6193aa53375fcd58929d613e45d14bcdb778567d1fd5e2d6e/azure_storage_blob-12.23.1-py3-none-any.whl", hash = "sha256:1c2238aa841d1545f42714a5017c010366137a44a0605da2d45f770174bfc6b4", size = 405622 },
]

[[package]]
name = "bcrypt"
version = "4.2.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/e4/7e/d95e7d96d4828e965891af92e43b52a4cd3395dc1c1ef4ee62748d0471d0/bcrypt-4.2.0.tar.gz", hash = "sha256:cf69eaf5185fd58f268f805b505ce31f9b9fc2d64b376642164e9244540c1221", size = 24294 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/a9/81/4e8f5bc0cd947e91fb720e1737371922854da47a94bc9630454e7b2845f8/bcrypt-4.2.0-cp37-abi3-macosx_10_12_universal2.whl", hash = "sha256:096a15d26ed6ce37a14c1ac1e48119660f21b24cba457f160a4b830f3fe6b5cb", size = 471568 },
    { url = "https://files.pythonhosted.org/packages/05/d2/1be1e16aedec04bcf8d0156e01b987d16a2063d38e64c3f28030a3427d61/bcrypt-4.2.0-cp37-abi3-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:c02d944ca89d9b1922ceb8a46460dd17df1ba37ab66feac4870f6862a1533c00", size = 277372 },
    { url = "https://files.pythonhosted.org/packages/e3/96/7a654027638ad9b7589effb6db77eb63eba64319dfeaf9c0f4ca953e5f76/bcrypt-4.2.0-cp37-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:1d84cf6d877918620b687b8fd1bf7781d11e8a0998f576c7aa939776b512b98d", size = 273488 },
    { url = "https://files.pythonhosted.org/packages/46/54/dc7b58abeb4a3d95bab653405935e27ba32f21b812d8ff38f271fb6f7f55/bcrypt-4.2.0-cp37-abi3-manylinux_2_28_aarch64.whl", hash = "sha256:1bb429fedbe0249465cdd85a58e8376f31bb315e484f16e68ca4c786dcc04291", size = 277759 },
    { url = "https://files.pythonhosted.org/packages/ac/be/da233c5f11fce3f8adec05e8e532b299b64833cc962f49331cdd0e614fa9/bcrypt-4.2.0-cp37-abi3-manylinux_2_28_x86_64.whl", hash = "sha256:655ea221910bcac76ea08aaa76df427ef8625f92e55a8ee44fbf7753dbabb328", size = 273796 },
    { url = "https://files.pythonhosted.org/packages/b0/b8/8b4add88d55a263cf1c6b8cf66c735280954a04223fcd2880120cc767ac3/bcrypt-4.2.0-cp37-abi3-musllinux_1_1_aarch64.whl", hash = "sha256:1ee38e858bf5d0287c39b7a1fc59eec64bbf880c7d504d3a06a96c16e14058e7", size = 311082 },
    { url = "https://files.pythonhosted.org/packages/7b/76/2aa660679abbdc7f8ee961552e4bb6415a81b303e55e9374533f22770203/bcrypt-4.2.0-cp37-abi3-musllinux_1_1_x86_64.whl", hash = "sha256:0da52759f7f30e83f1e30a888d9163a81353ef224d82dc58eb5bb52efcabc399", size = 305912 },
    { url = "https://files.pythonhosted.org/packages/00/03/2af7c45034aba6002d4f2b728c1a385676b4eab7d764410e34fd768009f2/bcrypt-4.2.0-cp37-abi3-musllinux_1_2_aarch64.whl", hash = "sha256:3698393a1b1f1fd5714524193849d0c6d524d33523acca37cd28f02899285060", size = 325185 },
    { url = "https://files.pythonhosted.org/packages/dc/5d/6843443ce4ab3af40bddb6c7c085ed4a8418b3396f7a17e60e6d9888416c/bcrypt-4.2.0-cp37-abi3-musllinux_1_2_x86_64.whl", hash = "sha256:762a2c5fb35f89606a9fde5e51392dad0cd1ab7ae64149a8b935fe8d79dd5ed7", size = 335188 },
    { url = "https://files.pythonhosted.org/packages/cb/4c/ff8ca83d816052fba36def1d24e97d9a85739b9bbf428c0d0ecd296a07c8/bcrypt-4.2.0-cp37-abi3-win32.whl", hash = "sha256:5a1e8aa9b28ae28020a3ac4b053117fb51c57a010b9f969603ed885f23841458", size = 156481 },
    { url = "https://files.pythonhosted.org/packages/65/f1/e09626c88a56cda488810fb29d5035f1662873777ed337880856b9d204ae/bcrypt-4.2.0-cp37-abi3-win_amd64.whl", hash = "sha256:8f6ede91359e5df88d1f5c1ef47428a4420136f3ce97763e31b86dd8280fbdf5", size = 151336 },
    { url = "https://files.pythonhosted.org/packages/96/86/8c6a84daed4dd878fbab094400c9174c43d9b838ace077a2f8ee8bc3ae12/bcrypt-4.2.0-cp39-abi3-macosx_10_12_universal2.whl", hash = "sha256:c52aac18ea1f4a4f65963ea4f9530c306b56ccd0c6f8c8da0c06976e34a6e841", size = 472414 },
    { url = "https://files.pythonhosted.org/packages/f6/05/e394515f4e23c17662e5aeb4d1859b11dc651be01a3bd03c2e919a155901/bcrypt-4.2.0-cp39-abi3-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:3bbbfb2734f0e4f37c5136130405332640a1e46e6b23e000eeff2ba8d005da68", size = 277599 },
    { url = "https://files.pythonhosted.org/packages/4b/3b/ad784eac415937c53da48983756105d267b91e56aa53ba8a1b2014b8d930/bcrypt-4.2.0-cp39-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:3413bd60460f76097ee2e0a493ccebe4a7601918219c02f503984f0a7ee0aebe", size = 273491 },
    { url = "https://files.pythonhosted.org/packages/cc/14/b9ff8e0218bee95e517b70e91130effb4511e8827ac1ab00b4e30943a3f6/bcrypt-4.2.0-cp39-abi3-manylinux_2_28_aarch64.whl", hash = "sha256:8d7bb9c42801035e61c109c345a28ed7e84426ae4865511eb82e913df18f58c2", size = 277934 },
    { url = "https://files.pythonhosted.org/packages/3e/d0/31938bb697600a04864246acde4918c4190a938f891fd11883eaaf41327a/bcrypt-4.2.0-cp39-abi3-manylinux_2_28_x86_64.whl", hash = "sha256:3d3a6d28cb2305b43feac298774b997e372e56c7c7afd90a12b3dc49b189151c", size = 273804 },
    { url = "https://files.pythonhosted.org/packages/e7/c3/dae866739989e3f04ae304e1201932571708cb292a28b2f1b93283e2dcd8/bcrypt-4.2.0-cp39-abi3-musllinux_1_1_aarch64.whl", hash = "sha256:9c1c4ad86351339c5f320ca372dfba6cb6beb25e8efc659bedd918d921956bae", size = 311275 },
    { url = "https://files.pythonhosted.org/packages/5d/2c/019bc2c63c6125ddf0483ee7d914a405860327767d437913942b476e9c9b/bcrypt-4.2.0-cp39-abi3-musllinux_1_1_x86_64.whl", hash = "sha256:27fe0f57bb5573104b5a6de5e4153c60814c711b29364c10a75a54bb6d7ff48d", size = 306355 },
    { url = "https://files.pythonhosted.org/packages/75/fe/9e137727f122bbe29771d56afbf4e0dbc85968caa8957806f86404a5bfe1/bcrypt-4.2.0-cp39-abi3-musllinux_1_2_aarch64.whl", hash = "sha256:8ac68872c82f1add6a20bd489870c71b00ebacd2e9134a8aa3f98a0052ab4b0e", size = 325381 },
    { url = "https://files.pythonhosted.org/packages/1a/d4/586b9c18a327561ea4cd336ff4586cca1a7aa0f5ee04e23a8a8bb9ca64f1/bcrypt-4.2.0-cp39-abi3-musllinux_1_2_x86_64.whl", hash = "sha256:cb2a8ec2bc07d3553ccebf0746bbf3d19426d1c6d1adbd4fa48925f66af7b9e8", size = 335685 },
    { url = "https://files.pythonhosted.org/packages/24/55/1a7127faf4576138bb278b91e9c75307490178979d69c8e6e273f74b974f/bcrypt-4.2.0-cp39-abi3-win32.whl", hash = "sha256:77800b7147c9dc905db1cba26abe31e504d8247ac73580b4aa179f98e6608f34", size = 155857 },
    { url = "https://files.pythonhosted.org/packages/1c/2a/c74052e54162ec639266d91539cca7cbf3d1d3b8b36afbfeaee0ea6a1702/bcrypt-4.2.0-cp39-abi3-win_amd64.whl", hash = "sha256:61ed14326ee023917ecd093ee6ef422a72f3aec6f07e21ea5f10622b735538a9", size = 151717 },
]

[[package]]
name = "blessed"
version = "1.20.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "jinxed", marker = "platform_system == 'Windows'" },
    { name = "six" },
    { name = "wcwidth" },
]
sdist = { url = "https://files.pythonhosted.org/packages/25/ae/92e9968ad23205389ec6bd82e2d4fca3817f1cdef34e10aa8d529ef8b1d7/blessed-1.20.0.tar.gz", hash = "sha256:2cdd67f8746e048f00df47a2880f4d6acbcdb399031b604e34ba8f71d5787680", size = 6655612 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/76/98/584f211c3a4bb38f2871fa937ee0cc83c130de50c955d6c7e2334dbf4acb/blessed-1.20.0-py2.py3-none-any.whl", hash = "sha256:0c542922586a265e699188e52d5f5ac5ec0dd517e5a1041d90d2bbf23f906058", size = 58372 },
]

[[package]]
name = "certifi"
version = "2024.8.30"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/b0/ee/9b19140fe824b367c04c5e1b369942dd754c4c5462d5674002f75c4dedc1/certifi-2024.8.30.tar.gz", hash = "sha256:bec941d2aa8195e248a60b31ff9f0558284cf01a52591ceda73ea9afffd69fd9", size = 168507 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/12/90/3c9ff0512038035f59d279fddeb79f5f1eccd8859f06d6163c58798b9487/certifi-2024.8.30-py3-none-any.whl", hash = "sha256:922820b53db7a7257ffbda3f597266d435245903d80737e34f8a45ff3e3230d8", size = 167321 },
]

[[package]]
name = "cffi"
version = "1.17.1"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "pycparser" },
]
sdist = { url = "https://files.pythonhosted.org/packages/fc/97/c783634659c2920c3fc70419e3af40972dbaf758daa229a7d6ea6135c90d/cffi-1.17.1.tar.gz", hash = "sha256:1c39c6016c32bc48dd54561950ebd6836e1670f2ae46128f67cf49e789c52824", size = 516621 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/6b/f4/927e3a8899e52a27fa57a48607ff7dc91a9ebe97399b357b85a0c7892e00/cffi-1.17.1-cp311-cp311-macosx_10_9_x86_64.whl", hash = "sha256:a45e3c6913c5b87b3ff120dcdc03f6131fa0065027d0ed7ee6190736a74cd401", size = 182264 },
    { url = "https://files.pythonhosted.org/packages/6c/f5/6c3a8efe5f503175aaddcbea6ad0d2c96dad6f5abb205750d1b3df44ef29/cffi-1.17.1-cp311-cp311-macosx_11_0_arm64.whl", hash = "sha256:30c5e0cb5ae493c04c8b42916e52ca38079f1b235c2f8ae5f4527b963c401caf", size = 178651 },
    { url = "https://files.pythonhosted.org/packages/94/dd/a3f0118e688d1b1a57553da23b16bdade96d2f9bcda4d32e7d2838047ff7/cffi-1.17.1-cp311-cp311-manylinux_2_12_i686.manylinux2010_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:f75c7ab1f9e4aca5414ed4d8e5c0e303a34f4421f8a0d47a4d019ceff0ab6af4", size = 445259 },
    { url = "https://files.pythonhosted.org/packages/2e/ea/70ce63780f096e16ce8588efe039d3c4f91deb1dc01e9c73a287939c79a6/cffi-1.17.1-cp311-cp311-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:a1ed2dd2972641495a3ec98445e09766f077aee98a1c896dcb4ad0d303628e41", size = 469200 },
    { url = "https://files.pythonhosted.org/packages/1c/a0/a4fa9f4f781bda074c3ddd57a572b060fa0df7655d2a4247bbe277200146/cffi-1.17.1-cp311-cp311-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:46bf43160c1a35f7ec506d254e5c890f3c03648a4dbac12d624e4490a7046cd1", size = 477235 },
    { url = "https://files.pythonhosted.org/packages/62/12/ce8710b5b8affbcdd5c6e367217c242524ad17a02fe5beec3ee339f69f85/cffi-1.17.1-cp311-cp311-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:a24ed04c8ffd54b0729c07cee15a81d964e6fee0e3d4d342a27b020d22959dc6", size = 459721 },
    { url = "https://files.pythonhosted.org/packages/ff/6b/d45873c5e0242196f042d555526f92aa9e0c32355a1be1ff8c27f077fd37/cffi-1.17.1-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:610faea79c43e44c71e1ec53a554553fa22321b65fae24889706c0a84d4ad86d", size = 467242 },
    { url = "https://files.pythonhosted.org/packages/1a/52/d9a0e523a572fbccf2955f5abe883cfa8bcc570d7faeee06336fbd50c9fc/cffi-1.17.1-cp311-cp311-musllinux_1_1_aarch64.whl", hash = "sha256:a9b15d491f3ad5d692e11f6b71f7857e7835eb677955c00cc0aefcd0669adaf6", size = 477999 },
    { url = "https://files.pythonhosted.org/packages/44/74/f2a2460684a1a2d00ca799ad880d54652841a780c4c97b87754f660c7603/cffi-1.17.1-cp311-cp311-musllinux_1_1_i686.whl", hash = "sha256:de2ea4b5833625383e464549fec1bc395c1bdeeb5f25c4a3a82b5a8c756ec22f", size = 454242 },
    { url = "https://files.pythonhosted.org/packages/f8/4a/34599cac7dfcd888ff54e801afe06a19c17787dfd94495ab0c8d35fe99fb/cffi-1.17.1-cp311-cp311-musllinux_1_1_x86_64.whl", hash = "sha256:fc48c783f9c87e60831201f2cce7f3b2e4846bf4d8728eabe54d60700b318a0b", size = 478604 },
    { url = "https://files.pythonhosted.org/packages/34/33/e1b8a1ba29025adbdcda5fb3a36f94c03d771c1b7b12f726ff7fef2ebe36/cffi-1.17.1-cp311-cp311-win32.whl", hash = "sha256:85a950a4ac9c359340d5963966e3e0a94a676bd6245a4b55bc43949eee26a655", size = 171727 },
    { url = "https://files.pythonhosted.org/packages/3d/97/50228be003bb2802627d28ec0627837ac0bf35c90cf769812056f235b2d1/cffi-1.17.1-cp311-cp311-win_amd64.whl", hash = "sha256:caaf0640ef5f5517f49bc275eca1406b0ffa6aa184892812030f04c2abf589a0", size = 181400 },
    { url = "https://files.pythonhosted.org/packages/5a/84/e94227139ee5fb4d600a7a4927f322e1d4aea6fdc50bd3fca8493caba23f/cffi-1.17.1-cp312-cp312-macosx_10_9_x86_64.whl", hash = "sha256:805b4371bf7197c329fcb3ead37e710d1bca9da5d583f5073b799d5c5bd1eee4", size = 183178 },
    { url = "https://files.pythonhosted.org/packages/da/ee/fb72c2b48656111c4ef27f0f91da355e130a923473bf5ee75c5643d00cca/cffi-1.17.1-cp312-cp312-macosx_11_0_arm64.whl", hash = "sha256:733e99bc2df47476e3848417c5a4540522f234dfd4ef3ab7fafdf555b082ec0c", size = 178840 },
    { url = "https://files.pythonhosted.org/packages/cc/b6/db007700f67d151abadf508cbfd6a1884f57eab90b1bb985c4c8c02b0f28/cffi-1.17.1-cp312-cp312-manylinux_2_12_i686.manylinux2010_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:1257bdabf294dceb59f5e70c64a3e2f462c30c7ad68092d01bbbfb1c16b1ba36", size = 454803 },
    { url = "https://files.pythonhosted.org/packages/1a/df/f8d151540d8c200eb1c6fba8cd0dfd40904f1b0682ea705c36e6c2e97ab3/cffi-1.17.1-cp312-cp312-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:da95af8214998d77a98cc14e3a3bd00aa191526343078b530ceb0bd710fb48a5", size = 478850 },
    { url = "https://files.pythonhosted.org/packages/28/c0/b31116332a547fd2677ae5b78a2ef662dfc8023d67f41b2a83f7c2aa78b1/cffi-1.17.1-cp312-cp312-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:d63afe322132c194cf832bfec0dc69a99fb9bb6bbd550f161a49e9e855cc78ff", size = 485729 },
    { url = "https://files.pythonhosted.org/packages/91/2b/9a1ddfa5c7f13cab007a2c9cc295b70fbbda7cb10a286aa6810338e60ea1/cffi-1.17.1-cp312-cp312-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:f79fc4fc25f1c8698ff97788206bb3c2598949bfe0fef03d299eb1b5356ada99", size = 471256 },
    { url = "https://files.pythonhosted.org/packages/b2/d5/da47df7004cb17e4955df6a43d14b3b4ae77737dff8bf7f8f333196717bf/cffi-1.17.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:b62ce867176a75d03a665bad002af8e6d54644fad99a3c70905c543130e39d93", size = 479424 },
    { url = "https://files.pythonhosted.org/packages/0b/ac/2a28bcf513e93a219c8a4e8e125534f4f6db03e3179ba1c45e949b76212c/cffi-1.17.1-cp312-cp312-musllinux_1_1_aarch64.whl", hash = "sha256:386c8bf53c502fff58903061338ce4f4950cbdcb23e2902d86c0f722b786bbe3", size = 484568 },
    { url = "https://files.pythonhosted.org/packages/d4/38/ca8a4f639065f14ae0f1d9751e70447a261f1a30fa7547a828ae08142465/cffi-1.17.1-cp312-cp312-musllinux_1_1_x86_64.whl", hash = "sha256:4ceb10419a9adf4460ea14cfd6bc43d08701f0835e979bf821052f1805850fe8", size = 488736 },
    { url = "https://files.pythonhosted.org/packages/86/c5/28b2d6f799ec0bdecf44dced2ec5ed43e0eb63097b0f58c293583b406582/cffi-1.17.1-cp312-cp312-win32.whl", hash = "sha256:a08d7e755f8ed21095a310a693525137cfe756ce62d066e53f502a83dc550f65", size = 172448 },
    { url = "https://files.pythonhosted.org/packages/50/b9/db34c4755a7bd1cb2d1603ac3863f22bcecbd1ba29e5ee841a4bc510b294/cffi-1.17.1-cp312-cp312-win_amd64.whl", hash = "sha256:51392eae71afec0d0c8fb1a53b204dbb3bcabcb3c9b807eedf3e1e6ccf2de903", size = 181976 },
]

[[package]]
name = "charset-normalizer"
version = "3.4.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/f2/4f/e1808dc01273379acc506d18f1504eb2d299bd4131743b9fc54d7be4df1e/charset_normalizer-3.4.0.tar.gz", hash = "sha256:223217c3d4f82c3ac5e29032b3f1c2eb0fb591b72161f86d93f5719079dae93e", size = 106620 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/9c/61/73589dcc7a719582bf56aae309b6103d2762b526bffe189d635a7fcfd998/charset_normalizer-3.4.0-cp311-cp311-macosx_10_9_universal2.whl", hash = "sha256:0d99dd8ff461990f12d6e42c7347fd9ab2532fb70e9621ba520f9e8637161d7c", size = 193339 },
    { url = "https://files.pythonhosted.org/packages/77/d5/8c982d58144de49f59571f940e329ad6e8615e1e82ef84584c5eeb5e1d72/charset_normalizer-3.4.0-cp311-cp311-macosx_10_9_x86_64.whl", hash = "sha256:c57516e58fd17d03ebe67e181a4e4e2ccab1168f8c2976c6a334d4f819fe5944", size = 124366 },
    { url = "https://files.pythonhosted.org/packages/bf/19/411a64f01ee971bed3231111b69eb56f9331a769072de479eae7de52296d/charset_normalizer-3.4.0-cp311-cp311-macosx_11_0_arm64.whl", hash = "sha256:6dba5d19c4dfab08e58d5b36304b3f92f3bd5d42c1a3fa37b5ba5cdf6dfcbcee", size = 118874 },
    { url = "https://files.pythonhosted.org/packages/4c/92/97509850f0d00e9f14a46bc751daabd0ad7765cff29cdfb66c68b6dad57f/charset_normalizer-3.4.0-cp311-cp311-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:bf4475b82be41b07cc5e5ff94810e6a01f276e37c2d55571e3fe175e467a1a1c", size = 138243 },
    { url = "https://files.pythonhosted.org/packages/e2/29/d227805bff72ed6d6cb1ce08eec707f7cfbd9868044893617eb331f16295/charset_normalizer-3.4.0-cp311-cp311-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:ce031db0408e487fd2775d745ce30a7cd2923667cf3b69d48d219f1d8f5ddeb6", size = 148676 },
    { url = "https://files.pythonhosted.org/packages/13/bc/87c2c9f2c144bedfa62f894c3007cd4530ba4b5351acb10dc786428a50f0/charset_normalizer-3.4.0-cp311-cp311-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:8ff4e7cdfdb1ab5698e675ca622e72d58a6fa2a8aa58195de0c0061288e6e3ea", size = 141289 },
    { url = "https://files.pythonhosted.org/packages/eb/5b/6f10bad0f6461fa272bfbbdf5d0023b5fb9bc6217c92bf068fa5a99820f5/charset_normalizer-3.4.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:3710a9751938947e6327ea9f3ea6332a09bf0ba0c09cae9cb1f250bd1f1549bc", size = 142585 },
    { url = "https://files.pythonhosted.org/packages/3b/a0/a68980ab8a1f45a36d9745d35049c1af57d27255eff8c907e3add84cf68f/charset_normalizer-3.4.0-cp311-cp311-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:82357d85de703176b5587dbe6ade8ff67f9f69a41c0733cf2425378b49954de5", size = 144408 },
    { url = "https://files.pythonhosted.org/packages/d7/a1/493919799446464ed0299c8eef3c3fad0daf1c3cd48bff9263c731b0d9e2/charset_normalizer-3.4.0-cp311-cp311-musllinux_1_2_aarch64.whl", hash = "sha256:47334db71978b23ebcf3c0f9f5ee98b8d65992b65c9c4f2d34c2eaf5bcaf0594", size = 139076 },
    { url = "https://files.pythonhosted.org/packages/fb/9d/9c13753a5a6e0db4a0a6edb1cef7aee39859177b64e1a1e748a6e3ba62c2/charset_normalizer-3.4.0-cp311-cp311-musllinux_1_2_i686.whl", hash = "sha256:8ce7fd6767a1cc5a92a639b391891bf1c268b03ec7e021c7d6d902285259685c", size = 146874 },
    { url = "https://files.pythonhosted.org/packages/75/d2/0ab54463d3410709c09266dfb416d032a08f97fd7d60e94b8c6ef54ae14b/charset_normalizer-3.4.0-cp311-cp311-musllinux_1_2_ppc64le.whl", hash = "sha256:f1a2f519ae173b5b6a2c9d5fa3116ce16e48b3462c8b96dfdded11055e3d6365", size = 150871 },
    { url = "https://files.pythonhosted.org/packages/8d/c9/27e41d481557be53d51e60750b85aa40eaf52b841946b3cdeff363105737/charset_normalizer-3.4.0-cp311-cp311-musllinux_1_2_s390x.whl", hash = "sha256:63bc5c4ae26e4bc6be6469943b8253c0fd4e4186c43ad46e713ea61a0ba49129", size = 148546 },
    { url = "https://files.pythonhosted.org/packages/ee/44/4f62042ca8cdc0cabf87c0fc00ae27cd8b53ab68be3605ba6d071f742ad3/charset_normalizer-3.4.0-cp311-cp311-musllinux_1_2_x86_64.whl", hash = "sha256:bcb4f8ea87d03bc51ad04add8ceaf9b0f085ac045ab4d74e73bbc2dc033f0236", size = 143048 },
    { url = "https://files.pythonhosted.org/packages/01/f8/38842422988b795220eb8038745d27a675ce066e2ada79516c118f291f07/charset_normalizer-3.4.0-cp311-cp311-win32.whl", hash = "sha256:9ae4ef0b3f6b41bad6366fb0ea4fc1d7ed051528e113a60fa2a65a9abb5b1d99", size = 94389 },
    { url = "https://files.pythonhosted.org/packages/0b/6e/b13bd47fa9023b3699e94abf565b5a2f0b0be6e9ddac9812182596ee62e4/charset_normalizer-3.4.0-cp311-cp311-win_amd64.whl", hash = "sha256:cee4373f4d3ad28f1ab6290684d8e2ebdb9e7a1b74fdc39e4c211995f77bec27", size = 101752 },
    { url = "https://files.pythonhosted.org/packages/d3/0b/4b7a70987abf9b8196845806198975b6aab4ce016632f817ad758a5aa056/charset_normalizer-3.4.0-cp312-cp312-macosx_10_13_universal2.whl", hash = "sha256:0713f3adb9d03d49d365b70b84775d0a0d18e4ab08d12bc46baa6132ba78aaf6", size = 194445 },
    { url = "https://files.pythonhosted.org/packages/50/89/354cc56cf4dd2449715bc9a0f54f3aef3dc700d2d62d1fa5bbea53b13426/charset_normalizer-3.4.0-cp312-cp312-macosx_10_13_x86_64.whl", hash = "sha256:de7376c29d95d6719048c194a9cf1a1b0393fbe8488a22008610b0361d834ecf", size = 125275 },
    { url = "https://files.pythonhosted.org/packages/fa/44/b730e2a2580110ced837ac083d8ad222343c96bb6b66e9e4e706e4d0b6df/charset_normalizer-3.4.0-cp312-cp312-macosx_11_0_arm64.whl", hash = "sha256:4a51b48f42d9358460b78725283f04bddaf44a9358197b889657deba38f329db", size = 119020 },
    { url = "https://files.pythonhosted.org/packages/9d/e4/9263b8240ed9472a2ae7ddc3e516e71ef46617fe40eaa51221ccd4ad9a27/charset_normalizer-3.4.0-cp312-cp312-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:b295729485b06c1a0683af02a9e42d2caa9db04a373dc38a6a58cdd1e8abddf1", size = 139128 },
    { url = "https://files.pythonhosted.org/packages/6b/e3/9f73e779315a54334240353eaea75854a9a690f3f580e4bd85d977cb2204/charset_normalizer-3.4.0-cp312-cp312-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:ee803480535c44e7f5ad00788526da7d85525cfefaf8acf8ab9a310000be4b03", size = 149277 },
    { url = "https://files.pythonhosted.org/packages/1a/cf/f1f50c2f295312edb8a548d3fa56a5c923b146cd3f24114d5adb7e7be558/charset_normalizer-3.4.0-cp312-cp312-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:3d59d125ffbd6d552765510e3f31ed75ebac2c7470c7274195b9161a32350284", size = 142174 },
    { url = "https://files.pythonhosted.org/packages/16/92/92a76dc2ff3a12e69ba94e7e05168d37d0345fa08c87e1fe24d0c2a42223/charset_normalizer-3.4.0-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:8cda06946eac330cbe6598f77bb54e690b4ca93f593dee1568ad22b04f347c15", size = 143838 },
    { url = "https://files.pythonhosted.org/packages/a4/01/2117ff2b1dfc61695daf2babe4a874bca328489afa85952440b59819e9d7/charset_normalizer-3.4.0-cp312-cp312-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:07afec21bbbbf8a5cc3651aa96b980afe2526e7f048fdfb7f1014d84acc8b6d8", size = 146149 },
    { url = "https://files.pythonhosted.org/packages/f6/9b/93a332b8d25b347f6839ca0a61b7f0287b0930216994e8bf67a75d050255/charset_normalizer-3.4.0-cp312-cp312-musllinux_1_2_aarch64.whl", hash = "sha256:6b40e8d38afe634559e398cc32b1472f376a4099c75fe6299ae607e404c033b2", size = 140043 },
    { url = "https://files.pythonhosted.org/packages/ab/f6/7ac4a01adcdecbc7a7587767c776d53d369b8b971382b91211489535acf0/charset_normalizer-3.4.0-cp312-cp312-musllinux_1_2_i686.whl", hash = "sha256:b8dcd239c743aa2f9c22ce674a145e0a25cb1566c495928440a181ca1ccf6719", size = 148229 },
    { url = "https://files.pythonhosted.org/packages/9d/be/5708ad18161dee7dc6a0f7e6cf3a88ea6279c3e8484844c0590e50e803ef/charset_normalizer-3.4.0-cp312-cp312-musllinux_1_2_ppc64le.whl", hash = "sha256:84450ba661fb96e9fd67629b93d2941c871ca86fc38d835d19d4225ff946a631", size = 151556 },
    { url = "https://files.pythonhosted.org/packages/5a/bb/3d8bc22bacb9eb89785e83e6723f9888265f3a0de3b9ce724d66bd49884e/charset_normalizer-3.4.0-cp312-cp312-musllinux_1_2_s390x.whl", hash = "sha256:44aeb140295a2f0659e113b31cfe92c9061622cadbc9e2a2f7b8ef6b1e29ef4b", size = 149772 },
    { url = "https://files.pythonhosted.org/packages/f7/fa/d3fc622de05a86f30beea5fc4e9ac46aead4731e73fd9055496732bcc0a4/charset_normalizer-3.4.0-cp312-cp312-musllinux_1_2_x86_64.whl", hash = "sha256:1db4e7fefefd0f548d73e2e2e041f9df5c59e178b4c72fbac4cc6f535cfb1565", size = 144800 },
    { url = "https://files.pythonhosted.org/packages/9a/65/bdb9bc496d7d190d725e96816e20e2ae3a6fa42a5cac99c3c3d6ff884118/charset_normalizer-3.4.0-cp312-cp312-win32.whl", hash = "sha256:5726cf76c982532c1863fb64d8c6dd0e4c90b6ece9feb06c9f202417a31f7dd7", size = 94836 },
    { url = "https://files.pythonhosted.org/packages/3e/67/7b72b69d25b89c0b3cea583ee372c43aa24df15f0e0f8d3982c57804984b/charset_normalizer-3.4.0-cp312-cp312-win_amd64.whl", hash = "sha256:b197e7094f232959f8f20541ead1d9862ac5ebea1d58e9849c1bf979255dfac9", size = 102187 },
    { url = "https://files.pythonhosted.org/packages/bf/9b/08c0432272d77b04803958a4598a51e2a4b51c06640af8b8f0f908c18bf2/charset_normalizer-3.4.0-py3-none-any.whl", hash = "sha256:fe9f97feb71aa9896b81973a7bbada8c49501dc73e58a10fcef6663af95e5079", size = 49446 },
]

[[package]]
name = "colorama"
version = "0.4.6"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/d8/53/6f443c9a4a8358a93a6792e2acffb9d9d5cb0a5cfd8802644b7b1c9a02e4/colorama-0.4.6.tar.gz", hash = "sha256:08695f5cb7ed6e0531a20572697297273c47b8cae5a63ffc6d6ed5c201be6e44", size = 27697 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/d1/d6/3965ed04c63042e047cb6a3e6ed1a63a35087b6a609aa3a15ed8ac56c221/colorama-0.4.6-py2.py3-none-any.whl", hash = "sha256:4f1d9991f5acc0ca119f9d443620b77f9d6b33703e51011c16baf57afb285fc6", size = 25335 },
]

[[package]]
name = "cryptg"
version = "0.5.0.post0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/8f/c8/9570ac88c1f14bc7a944819da523fdcdba54064ac49dd5faec86f8bf4c95/cryptg-0.5.0.post0.tar.gz", hash = "sha256:be5b36e662a73c9b2f1e02e4f0d71b0f97870e514e924d5988d7253a780e3a7b", size = 13395 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/46/ab/710797be0833e92b3d53f5ec50c082a6d764f971dd52441a68c5761ec53c/cryptg-0.5.0.post0-cp311-cp311-macosx_11_0_arm64.whl", hash = "sha256:d82293ea2515fe38300824fc075f5d4ec3e0fd3142a9ada1d88dae4f553eefec", size = 205458 },
    { url = "https://files.pythonhosted.org/packages/0c/aa/c96a044423b82a1259915cc2097ef02e5ef61b348a06c21e0de8a769c666/cryptg-0.5.0.post0-cp311-cp311-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:c2c066b4a2ee4ed90298d557cac19db9c834bd7e4e8435a1e024393155b850bf", size = 236207 },
    { url = "https://files.pythonhosted.org/packages/3c/45/f15e458fe7d75a902b87f5f57c64d1ed816597b8d390afde3bfc618a9a4f/cryptg-0.5.0.post0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:209cf9a499e9cdb91580c8a5f9a3b7e475514016352350aea3d0a58656d4c2fe", size = 238256 },
    { url = "https://files.pythonhosted.org/packages/c0/a5/c82ff94b5cec77c8befc1228863aac06f61bfe71c76d3044559c6f098485/cryptg-0.5.0.post0-cp311-cp311-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:f6e144749355ee2a3473a2c295f8178b58e8bbf127d45bbc670a30df0e44b27b", size = 259084 },
    { url = "https://files.pythonhosted.org/packages/1f/b1/acbe296f928916cfb8ab090bdedfa7992f9cf26d8a35485bdbfedc69dcd9/cryptg-0.5.0.post0-cp311-cp311-win32.whl", hash = "sha256:2ea4ac6a1b8677c41b0df368be7779ed19b07ef033a290d35b0bf2d202a34ca9", size = 113276 },
    { url = "https://files.pythonhosted.org/packages/53/d9/0549b73de6ae9db684baa44a1efe9057103215908de9386e907cc615d2a3/cryptg-0.5.0.post0-cp311-cp311-win_amd64.whl", hash = "sha256:882f12602db8d1021271a83275fb5b56bd6dbea22a6de086c26f4a22263d6c53", size = 111602 },
    { url = "https://files.pythonhosted.org/packages/f4/6e/edc3e88c068025bd3218ad1f96158cc3e18a684df97da28eea2bfb258b28/cryptg-0.5.0.post0-cp312-cp312-macosx_11_0_arm64.whl", hash = "sha256:39795b25237da4ca6140cf4c2924807bfb683e528823ebbbae45b95f174ec903", size = 204976 },
    { url = "https://files.pythonhosted.org/packages/01/84/23fc82ee92cd785a56bf57770ed972e9bb8a0bc50342fac0ee4971a63a82/cryptg-0.5.0.post0-cp312-cp312-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:84f6b6f623d894ff88429805b7a1670f43df7dd05a71edc2f3c7b34175182c99", size = 235585 },
    { url = "https://files.pythonhosted.org/packages/d4/b0/9ae39034b7542fe1a4e05a8c41fbf24e27176d6de46683d64478cff223e3/cryptg-0.5.0.post0-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:9107b7daf308b453f00635f0491e4e658034925f19aa8d6623c73fe4e5764178", size = 237675 },
    { url = "https://files.pythonhosted.org/packages/bb/fd/b55b0f4d8de615ce832d5fc9e77c1344c81695c97d22196c8c22b5f23c39/cryptg-0.5.0.post0-cp312-cp312-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:96da29d91bab292a7f91c43e27367529b5e9e81c894ceea29055460d0fe86346", size = 258590 },
    { url = "https://files.pythonhosted.org/packages/20/af/8f1c82f22ad48de537bfdc82e549dd1470f854fdf855bf6e8ca1f79cdcda/cryptg-0.5.0.post0-cp312-cp312-win32.whl", hash = "sha256:2ff7f381746f0fcec3b8a25f5d39b9f7c84d7c59d5d27d5c4d53c6b2ba927a98", size = 113315 },
    { url = "https://files.pythonhosted.org/packages/e8/09/86367b6e9433cc7a0c6c50c1b71b251166719dfadd17dbcbec5f82908b72/cryptg-0.5.0.post0-cp312-cp312-win_amd64.whl", hash = "sha256:cef8ed1144e11b3fbb85c2bddac45a783fedec7e7a78980b195a9b217087c619", size = 111400 },
]

[[package]]
name = "cryptography"
version = "43.0.3"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "cffi", marker = "platform_python_implementation != 'PyPy'" },
]
sdist = { url = "https://files.pythonhosted.org/packages/0d/05/07b55d1fa21ac18c3a8c79f764e2514e6f6a9698f1be44994f5adf0d29db/cryptography-43.0.3.tar.gz", hash = "sha256:315b9001266a492a6ff443b61238f956b214dbec9910a081ba5b6646a055a805", size = 686989 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/1f/f3/01fdf26701a26f4b4dbc337a26883ad5bccaa6f1bbbdd29cd89e22f18a1c/cryptography-43.0.3-cp37-abi3-macosx_10_9_universal2.whl", hash = "sha256:bf7a1932ac4176486eab36a19ed4c0492da5d97123f1406cf15e41b05e787d2e", size = 6225303 },
    { url = "https://files.pythonhosted.org/packages/a3/01/4896f3d1b392025d4fcbecf40fdea92d3df8662123f6835d0af828d148fd/cryptography-43.0.3-cp37-abi3-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:63efa177ff54aec6e1c0aefaa1a241232dcd37413835a9b674b6e3f0ae2bfd3e", size = 3760905 },
    { url = "https://files.pythonhosted.org/packages/0a/be/f9a1f673f0ed4b7f6c643164e513dbad28dd4f2dcdf5715004f172ef24b6/cryptography-43.0.3-cp37-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:7e1ce50266f4f70bf41a2c6dc4358afadae90e2a1e5342d3c08883df1675374f", size = 3977271 },
    { url = "https://files.pythonhosted.org/packages/4e/49/80c3a7b5514d1b416d7350830e8c422a4d667b6d9b16a9392ebfd4a5388a/cryptography-43.0.3-cp37-abi3-manylinux_2_28_aarch64.whl", hash = "sha256:443c4a81bb10daed9a8f334365fe52542771f25aedaf889fd323a853ce7377d6", size = 3746606 },
    { url = "https://files.pythonhosted.org/packages/0e/16/a28ddf78ac6e7e3f25ebcef69ab15c2c6be5ff9743dd0709a69a4f968472/cryptography-43.0.3-cp37-abi3-manylinux_2_28_x86_64.whl", hash = "sha256:74f57f24754fe349223792466a709f8e0c093205ff0dca557af51072ff47ab18", size = 3986484 },
    { url = "https://files.pythonhosted.org/packages/01/f5/69ae8da70c19864a32b0315049866c4d411cce423ec169993d0434218762/cryptography-43.0.3-cp37-abi3-musllinux_1_2_aarch64.whl", hash = "sha256:9762ea51a8fc2a88b70cf2995e5675b38d93bf36bd67d91721c309df184f49bd", size = 3852131 },
    { url = "https://files.pythonhosted.org/packages/fd/db/e74911d95c040f9afd3612b1f732e52b3e517cb80de8bf183be0b7d413c6/cryptography-43.0.3-cp37-abi3-musllinux_1_2_x86_64.whl", hash = "sha256:81ef806b1fef6b06dcebad789f988d3b37ccaee225695cf3e07648eee0fc6b73", size = 4075647 },
    { url = "https://files.pythonhosted.org/packages/56/48/7b6b190f1462818b324e674fa20d1d5ef3e24f2328675b9b16189cbf0b3c/cryptography-43.0.3-cp37-abi3-win32.whl", hash = "sha256:cbeb489927bd7af4aa98d4b261af9a5bc025bd87f0e3547e11584be9e9427be2", size = 2623873 },
    { url = "https://files.pythonhosted.org/packages/eb/b1/0ebff61a004f7f89e7b65ca95f2f2375679d43d0290672f7713ee3162aff/cryptography-43.0.3-cp37-abi3-win_amd64.whl", hash = "sha256:f46304d6f0c6ab8e52770addfa2fc41e6629495548862279641972b6215451cd", size = 3068039 },
    { url = "https://files.pythonhosted.org/packages/30/d5/c8b32c047e2e81dd172138f772e81d852c51f0f2ad2ae8a24f1122e9e9a7/cryptography-43.0.3-cp39-abi3-macosx_10_9_universal2.whl", hash = "sha256:8ac43ae87929a5982f5948ceda07001ee5e83227fd69cf55b109144938d96984", size = 6222984 },
    { url = "https://files.pythonhosted.org/packages/2f/78/55356eb9075d0be6e81b59f45c7b48df87f76a20e73893872170471f3ee8/cryptography-43.0.3-cp39-abi3-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:846da004a5804145a5f441b8530b4bf35afbf7da70f82409f151695b127213d5", size = 3762968 },
    { url = "https://files.pythonhosted.org/packages/2a/2c/488776a3dc843f95f86d2f957ca0fc3407d0242b50bede7fad1e339be03f/cryptography-43.0.3-cp39-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:0f996e7268af62598f2fc1204afa98a3b5712313a55c4c9d434aef49cadc91d4", size = 3977754 },
    { url = "https://files.pythonhosted.org/packages/7c/04/2345ca92f7a22f601a9c62961741ef7dd0127c39f7310dffa0041c80f16f/cryptography-43.0.3-cp39-abi3-manylinux_2_28_aarch64.whl", hash = "sha256:f7b178f11ed3664fd0e995a47ed2b5ff0a12d893e41dd0494f406d1cf555cab7", size = 3749458 },
    { url = "https://files.pythonhosted.org/packages/ac/25/e715fa0bc24ac2114ed69da33adf451a38abb6f3f24ec207908112e9ba53/cryptography-43.0.3-cp39-abi3-manylinux_2_28_x86_64.whl", hash = "sha256:c2e6fc39c4ab499049df3bdf567f768a723a5e8464816e8f009f121a5a9f4405", size = 3988220 },
    { url = "https://files.pythonhosted.org/packages/21/ce/b9c9ff56c7164d8e2edfb6c9305045fbc0df4508ccfdb13ee66eb8c95b0e/cryptography-43.0.3-cp39-abi3-musllinux_1_2_aarch64.whl", hash = "sha256:e1be4655c7ef6e1bbe6b5d0403526601323420bcf414598955968c9ef3eb7d16", size = 3853898 },
    { url = "https://files.pythonhosted.org/packages/2a/33/b3682992ab2e9476b9c81fff22f02c8b0a1e6e1d49ee1750a67d85fd7ed2/cryptography-43.0.3-cp39-abi3-musllinux_1_2_x86_64.whl", hash = "sha256:df6b6c6d742395dd77a23ea3728ab62f98379eff8fb61be2744d4679ab678f73", size = 4076592 },
    { url = "https://files.pythonhosted.org/packages/81/1e/ffcc41b3cebd64ca90b28fd58141c5f68c83d48563c88333ab660e002cd3/cryptography-43.0.3-cp39-abi3-win32.whl", hash = "sha256:d56e96520b1020449bbace2b78b603442e7e378a9b3bd68de65c782db1507995", size = 2623145 },
    { url = "https://files.pythonhosted.org/packages/87/5c/3dab83cc4aba1f4b0e733e3f0c3e7d4386440d660ba5b1e3ff995feb734d/cryptography-43.0.3-cp39-abi3-win_amd64.whl", hash = "sha256:0c580952eef9bf68c4747774cde7ec1d85a6e61de97281f2dba83c7d2c806362", size = 3068026 },
]

[[package]]
name = "distro"
version = "1.9.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/fc/f8/98eea607f65de6527f8a2e8885fc8015d3e6f5775df186e443e0964a11c3/distro-1.9.0.tar.gz", hash = "sha256:2fa77c6fd8940f116ee1d6b94a2f90b13b5ea8d019b98bc8bafdcabcdd9bdbed", size = 60722 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/12/b3/231ffd4ab1fc9d679809f356cebee130ac7daa00d6d6f3206dd4fd137e9e/distro-1.9.0-py3-none-any.whl", hash = "sha256:7bffd925d65168f85027d8da9af6bddab658135b840670a223589bc0c8ef02b2", size = 20277 },
]

[[package]]
name = "dsutil"
version = "1.0.0"
source = { editable = "." }
dependencies = [
    { name = "aiohttp" },
    { name = "argparse" },
    { name = "azure-storage-blob" },
    { name = "colorama" },
    { name = "cryptg" },
    { name = "distro" },
    { name = "halo" },
    { name = "inquirer" },
    { name = "mutagen" },
    { name = "natsort" },
    { name = "numpy" },
    { name = "paramiko" },
    { name = "path" },
    { name = "path-py" },
    { name = "pathlib" },
    { name = "pexpect" },
    { name = "pillow" },
    { name = "pycountry" },
    { name = "pydub" },
    { name = "pyperclip" },
    { name = "pyreadline" },
    { name = "python-dotenv" },
    { name = "readchar" },
    { name = "requests" },
    { name = "rich" },
    { name = "scipy" },
    { name = "scp" },
    { name = "send2trash" },
    { name = "soundfile" },
    { name = "telethon" },
    { name = "termcolor" },
    { name = "tomlkit" },
    { name = "tqdm" },
]

[package.optional-dependencies]
dev = [
    { name = "mypy" },
    { name = "ruff" },
    { name = "setuptools" },
    { name = "types-paramiko" },
    { name = "types-pillow" },
    { name = "types-requests" },
    { name = "types-send2trash" },
]

[package.metadata]
requires-dist = [
    { name = "aiohttp", specifier = ">=3.10.0" },
    { name = "argparse", specifier = ">=1.4.0" },
    { name = "azure-storage-blob", specifier = ">=12.20.0" },
    { name = "colorama", specifier = ">=0.4.6" },
    { name = "cryptg", specifier = ">=0.4.0" },
    { name = "distro", specifier = ">=1.9.0" },
    { name = "dsutil", directory = "dsutil" },
    { name = "halo", specifier = ">=0.0.31" },
    { name = "inquirer", specifier = ">=3.2.4" },
    { name = "mutagen", specifier = ">=1.47.0" },
    { name = "mypy", marker = "extra == 'dev'", specifier = ">=1.10.0" },
    { name = "natsort", specifier = ">=8.4.0" },
    { name = "numpy", specifier = ">=1.26.4" },
    { name = "paramiko", specifier = ">=3.4.0" },
    { name = "path", specifier = ">=17.0.0" },
    { name = "path-py", specifier = ">=12.5.0" },
    { name = "pathlib", specifier = ">=1.0.1" },
    { name = "pexpect", specifier = ">=4.9.0" },
    { name = "pillow", specifier = ">=10.3.0" },
    { name = "pycountry", specifier = ">=23.12.11" },
    { name = "pydub", specifier = ">=0.25.1" },
    { name = "pyperclip", specifier = ">=1.8.2" },
    { name = "pyreadline", specifier = ">=2.1" },
    { name = "python-dotenv", specifier = ">=1.0.1" },
    { name = "readchar", specifier = ">=4.1.0" },
    { name = "requests", specifier = ">=2.32.2" },
    { name = "rich", specifier = ">=13.8.1" },
    { name = "ruff", marker = "extra == 'dev'", specifier = ">=0.7.0" },
    { name = "scipy", specifier = ">=1.13.1" },
    { name = "scp", specifier = ">=0.15.0" },
    { name = "send2trash", specifier = ">=1.8.3" },
    { name = "setuptools", marker = "extra == 'dev'", specifier = ">=70.0.0" },
    { name = "soundfile", specifier = ">=0.12.1" },
    { name = "telethon", specifier = ">=1.36.0" },
    { name = "termcolor", specifier = ">=2.4.0" },
    { name = "tomlkit", specifier = ">=0.13.2" },
    { name = "tqdm", specifier = ">=4.66.4" },
    { name = "types-paramiko", marker = "extra == 'dev'", specifier = ">=3.4.0.20240423" },
    { name = "types-pillow", marker = "extra == 'dev'", specifier = ">=10.2.0.20240520" },
    { name = "types-requests", marker = "extra == 'dev'", specifier = ">=2.32.0.20240523" },
    { name = "types-send2trash", marker = "extra == 'dev'", specifier = ">=1.8.2.7" },
]

[[package]]
name = "editor"
version = "1.6.6"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "runs" },
    { name = "xmod" },
]
sdist = { url = "https://files.pythonhosted.org/packages/2a/92/734a4ab345914259cb6146fd36512608ea42be16195375c379046f33283d/editor-1.6.6.tar.gz", hash = "sha256:bb6989e872638cd119db9a4fce284cd8e13c553886a1c044c6b8d8a160c871f8", size = 3197 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/1b/c2/4bc8cd09b14e28ce3f406a8b05761bed0d785d1ca8c2a5c6684d884c66a2/editor-1.6.6-py3-none-any.whl", hash = "sha256:e818e6913f26c2a81eadef503a2741d7cca7f235d20e217274a009ecd5a74abf", size = 4017 },
]

[[package]]
name = "frozenlist"
version = "1.5.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/8f/ed/0f4cec13a93c02c47ec32d81d11c0c1efbadf4a471e3f3ce7cad366cbbd3/frozenlist-1.5.0.tar.gz", hash = "sha256:81d5af29e61b9c8348e876d442253723928dce6433e0e76cd925cd83f1b4b817", size = 39930 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/79/43/0bed28bf5eb1c9e4301003b74453b8e7aa85fb293b31dde352aac528dafc/frozenlist-1.5.0-cp311-cp311-macosx_10_9_universal2.whl", hash = "sha256:fd74520371c3c4175142d02a976aee0b4cb4a7cc912a60586ffd8d5929979b30", size = 94987 },
    { url = "https://files.pythonhosted.org/packages/bb/bf/b74e38f09a246e8abbe1e90eb65787ed745ccab6eaa58b9c9308e052323d/frozenlist-1.5.0-cp311-cp311-macosx_10_9_x86_64.whl", hash = "sha256:2f3f7a0fbc219fb4455264cae4d9f01ad41ae6ee8524500f381de64ffaa077d5", size = 54584 },
    { url = "https://files.pythonhosted.org/packages/2c/31/ab01375682f14f7613a1ade30149f684c84f9b8823a4391ed950c8285656/frozenlist-1.5.0-cp311-cp311-macosx_11_0_arm64.whl", hash = "sha256:f47c9c9028f55a04ac254346e92977bf0f166c483c74b4232bee19a6697e4778", size = 52499 },
    { url = "https://files.pythonhosted.org/packages/98/a8/d0ac0b9276e1404f58fec3ab6e90a4f76b778a49373ccaf6a563f100dfbc/frozenlist-1.5.0-cp311-cp311-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:0996c66760924da6e88922756d99b47512a71cfd45215f3570bf1e0b694c206a", size = 276357 },
    { url = "https://files.pythonhosted.org/packages/ad/c9/c7761084fa822f07dac38ac29f841d4587570dd211e2262544aa0b791d21/frozenlist-1.5.0-cp311-cp311-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:a2fe128eb4edeabe11896cb6af88fca5346059f6c8d807e3b910069f39157869", size = 287516 },
    { url = "https://files.pythonhosted.org/packages/a1/ff/cd7479e703c39df7bdab431798cef89dc75010d8aa0ca2514c5b9321db27/frozenlist-1.5.0-cp311-cp311-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:1a8ea951bbb6cacd492e3948b8da8c502a3f814f5d20935aae74b5df2b19cf3d", size = 283131 },
    { url = "https://files.pythonhosted.org/packages/59/a0/370941beb47d237eca4fbf27e4e91389fd68699e6f4b0ebcc95da463835b/frozenlist-1.5.0-cp311-cp311-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:de537c11e4aa01d37db0d403b57bd6f0546e71a82347a97c6a9f0dcc532b3a45", size = 261320 },
    { url = "https://files.pythonhosted.org/packages/b8/5f/c10123e8d64867bc9b4f2f510a32042a306ff5fcd7e2e09e5ae5100ee333/frozenlist-1.5.0-cp311-cp311-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:9c2623347b933fcb9095841f1cc5d4ff0b278addd743e0e966cb3d460278840d", size = 274877 },
    { url = "https://files.pythonhosted.org/packages/fa/79/38c505601ae29d4348f21706c5d89755ceded02a745016ba2f58bd5f1ea6/frozenlist-1.5.0-cp311-cp311-musllinux_1_2_aarch64.whl", hash = "sha256:cee6798eaf8b1416ef6909b06f7dc04b60755206bddc599f52232606e18179d3", size = 269592 },
    { url = "https://files.pythonhosted.org/packages/19/e2/39f3a53191b8204ba9f0bb574b926b73dd2efba2a2b9d2d730517e8f7622/frozenlist-1.5.0-cp311-cp311-musllinux_1_2_i686.whl", hash = "sha256:f5f9da7f5dbc00a604fe74aa02ae7c98bcede8a3b8b9666f9f86fc13993bc71a", size = 265934 },
    { url = "https://files.pythonhosted.org/packages/d5/c9/3075eb7f7f3a91f1a6b00284af4de0a65a9ae47084930916f5528144c9dd/frozenlist-1.5.0-cp311-cp311-musllinux_1_2_ppc64le.whl", hash = "sha256:90646abbc7a5d5c7c19461d2e3eeb76eb0b204919e6ece342feb6032c9325ae9", size = 283859 },
    { url = "https://files.pythonhosted.org/packages/05/f5/549f44d314c29408b962fa2b0e69a1a67c59379fb143b92a0a065ffd1f0f/frozenlist-1.5.0-cp311-cp311-musllinux_1_2_s390x.whl", hash = "sha256:bdac3c7d9b705d253b2ce370fde941836a5f8b3c5c2b8fd70940a3ea3af7f4f2", size = 287560 },
    { url = "https://files.pythonhosted.org/packages/9d/f8/cb09b3c24a3eac02c4c07a9558e11e9e244fb02bf62c85ac2106d1eb0c0b/frozenlist-1.5.0-cp311-cp311-musllinux_1_2_x86_64.whl", hash = "sha256:03d33c2ddbc1816237a67f66336616416e2bbb6beb306e5f890f2eb22b959cdf", size = 277150 },
    { url = "https://files.pythonhosted.org/packages/37/48/38c2db3f54d1501e692d6fe058f45b6ad1b358d82cd19436efab80cfc965/frozenlist-1.5.0-cp311-cp311-win32.whl", hash = "sha256:237f6b23ee0f44066219dae14c70ae38a63f0440ce6750f868ee08775073f942", size = 45244 },
    { url = "https://files.pythonhosted.org/packages/ca/8c/2ddffeb8b60a4bce3b196c32fcc30d8830d4615e7b492ec2071da801b8ad/frozenlist-1.5.0-cp311-cp311-win_amd64.whl", hash = "sha256:0cc974cc93d32c42e7b0f6cf242a6bd941c57c61b618e78b6c0a96cb72788c1d", size = 51634 },
    { url = "https://files.pythonhosted.org/packages/79/73/fa6d1a96ab7fd6e6d1c3500700963eab46813847f01ef0ccbaa726181dd5/frozenlist-1.5.0-cp312-cp312-macosx_10_13_universal2.whl", hash = "sha256:31115ba75889723431aa9a4e77d5f398f5cf976eea3bdf61749731f62d4a4a21", size = 94026 },
    { url = "https://files.pythonhosted.org/packages/ab/04/ea8bf62c8868b8eada363f20ff1b647cf2e93377a7b284d36062d21d81d1/frozenlist-1.5.0-cp312-cp312-macosx_10_13_x86_64.whl", hash = "sha256:7437601c4d89d070eac8323f121fcf25f88674627505334654fd027b091db09d", size = 54150 },
    { url = "https://files.pythonhosted.org/packages/d0/9a/8e479b482a6f2070b26bda572c5e6889bb3ba48977e81beea35b5ae13ece/frozenlist-1.5.0-cp312-cp312-macosx_11_0_arm64.whl", hash = "sha256:7948140d9f8ece1745be806f2bfdf390127cf1a763b925c4a805c603df5e697e", size = 51927 },
    { url = "https://files.pythonhosted.org/packages/e3/12/2aad87deb08a4e7ccfb33600871bbe8f0e08cb6d8224371387f3303654d7/frozenlist-1.5.0-cp312-cp312-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:feeb64bc9bcc6b45c6311c9e9b99406660a9c05ca8a5b30d14a78555088b0b3a", size = 282647 },
    { url = "https://files.pythonhosted.org/packages/77/f2/07f06b05d8a427ea0060a9cef6e63405ea9e0d761846b95ef3fb3be57111/frozenlist-1.5.0-cp312-cp312-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:683173d371daad49cffb8309779e886e59c2f369430ad28fe715f66d08d4ab1a", size = 289052 },
    { url = "https://files.pythonhosted.org/packages/bd/9f/8bf45a2f1cd4aa401acd271b077989c9267ae8463e7c8b1eb0d3f561b65e/frozenlist-1.5.0-cp312-cp312-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:7d57d8f702221405a9d9b40f9da8ac2e4a1a8b5285aac6100f3393675f0a85ee", size = 291719 },
    { url = "https://files.pythonhosted.org/packages/41/d1/1f20fd05a6c42d3868709b7604c9f15538a29e4f734c694c6bcfc3d3b935/frozenlist-1.5.0-cp312-cp312-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:30c72000fbcc35b129cb09956836c7d7abf78ab5416595e4857d1cae8d6251a6", size = 267433 },
    { url = "https://files.pythonhosted.org/packages/af/f2/64b73a9bb86f5a89fb55450e97cd5c1f84a862d4ff90d9fd1a73ab0f64a5/frozenlist-1.5.0-cp312-cp312-manylinux_2_5_x86_64.manylinux1_x86_64.manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:000a77d6034fbad9b6bb880f7ec073027908f1b40254b5d6f26210d2dab1240e", size = 283591 },
    { url = "https://files.pythonhosted.org/packages/29/e2/ffbb1fae55a791fd6c2938dd9ea779509c977435ba3940b9f2e8dc9d5316/frozenlist-1.5.0-cp312-cp312-musllinux_1_2_aarch64.whl", hash = "sha256:5d7f5a50342475962eb18b740f3beecc685a15b52c91f7d975257e13e029eca9", size = 273249 },
    { url = "https://files.pythonhosted.org/packages/2e/6e/008136a30798bb63618a114b9321b5971172a5abddff44a100c7edc5ad4f/frozenlist-1.5.0-cp312-cp312-musllinux_1_2_i686.whl", hash = "sha256:87f724d055eb4785d9be84e9ebf0f24e392ddfad00b3fe036e43f489fafc9039", size = 271075 },
    { url = "https://files.pythonhosted.org/packages/ae/f0/4e71e54a026b06724cec9b6c54f0b13a4e9e298cc8db0f82ec70e151f5ce/frozenlist-1.5.0-cp312-cp312-musllinux_1_2_ppc64le.whl", hash = "sha256:6e9080bb2fb195a046e5177f10d9d82b8a204c0736a97a153c2466127de87784", size = 285398 },
    { url = "https://files.pythonhosted.org/packages/4d/36/70ec246851478b1c0b59f11ef8ade9c482ff447c1363c2bd5fad45098b12/frozenlist-1.5.0-cp312-cp312-musllinux_1_2_s390x.whl", hash = "sha256:9b93d7aaa36c966fa42efcaf716e6b3900438632a626fb09c049f6a2f09fc631", size = 294445 },
    { url = "https://files.pythonhosted.org/packages/37/e0/47f87544055b3349b633a03c4d94b405956cf2437f4ab46d0928b74b7526/frozenlist-1.5.0-cp312-cp312-musllinux_1_2_x86_64.whl", hash = "sha256:52ef692a4bc60a6dd57f507429636c2af8b6046db8b31b18dac02cbc8f507f7f", size = 280569 },
    { url = "https://files.pythonhosted.org/packages/f9/7c/490133c160fb6b84ed374c266f42800e33b50c3bbab1652764e6e1fc498a/frozenlist-1.5.0-cp312-cp312-win32.whl", hash = "sha256:29d94c256679247b33a3dc96cce0f93cbc69c23bf75ff715919332fdbb6a32b8", size = 44721 },
    { url = "https://files.pythonhosted.org/packages/b1/56/4e45136ffc6bdbfa68c29ca56ef53783ef4c2fd395f7cbf99a2624aa9aaa/frozenlist-1.5.0-cp312-cp312-win_amd64.whl", hash = "sha256:8969190d709e7c48ea386db202d708eb94bdb29207a1f269bab1196ce0dcca1f", size = 51329 },
    { url = "https://files.pythonhosted.org/packages/c6/c8/a5be5b7550c10858fcf9b0ea054baccab474da77d37f1e828ce043a3a5d4/frozenlist-1.5.0-py3-none-any.whl", hash = "sha256:d994863bba198a4a518b467bb971c56e1db3f180a25c6cf7bb1949c267f748c3", size = 11901 },
]

[[package]]
name = "halo"
version = "0.0.31"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "colorama" },
    { name = "log-symbols" },
    { name = "six" },
    { name = "spinners" },
    { name = "termcolor" },
]
sdist = { url = "https://files.pythonhosted.org/packages/ee/48/d53580d30b1fabf25d0d1fcc3f5b26d08d2ac75a1890ff6d262f9f027436/halo-0.0.31.tar.gz", hash = "sha256:7b67a3521ee91d53b7152d4ee3452811e1d2a6321975137762eb3d70063cc9d6", size = 11666 }

[[package]]
name = "idna"
version = "3.10"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/f1/70/7703c29685631f5a7590aa73f1f1d3fa9a380e654b86af429e0934a32f7d/idna-3.10.tar.gz", hash = "sha256:12f65c9b470abda6dc35cf8e63cc574b1c52b11df2c86030af0ac09b01b13ea9", size = 190490 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/76/c6/c88e154df9c4e1a2a66ccf0005a88dfb2650c1dffb6f5ce603dfbd452ce3/idna-3.10-py3-none-any.whl", hash = "sha256:946d195a0d259cbba61165e88e65941f16e9b36ea6ddb97f00452bae8b1287d3", size = 70442 },
]

[[package]]
name = "inquirer"
version = "3.4.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "blessed" },
    { name = "editor" },
    { name = "readchar" },
]
sdist = { url = "https://files.pythonhosted.org/packages/f3/06/ef91eb8f3feafb736aa33dcb278fc9555d17861aa571b684715d095db24d/inquirer-3.4.0.tar.gz", hash = "sha256:8edc99c076386ee2d2204e5e3653c2488244e82cb197b2d498b3c1b5ffb25d0b", size = 14472 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/a4/b2/be907c8c0f8303bc4b10089f5470014c3bf3521e9b8d3decf3037fd94725/inquirer-3.4.0-py3-none-any.whl", hash = "sha256:bb0ec93c833e4ce7b51b98b1644b0a4d2bb39755c39787f6a504e4fee7a11b60", size = 18077 },
]

[[package]]
name = "isodate"
version = "0.7.2"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/54/4d/e940025e2ce31a8ce1202635910747e5a87cc3a6a6bb2d00973375014749/isodate-0.7.2.tar.gz", hash = "sha256:4cd1aa0f43ca76f4a6c6c0292a85f40b35ec2e43e315b59f06e6d32171a953e6", size = 29705 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/15/aa/0aca39a37d3c7eb941ba736ede56d689e7be91cab5d9ca846bde3999eba6/isodate-0.7.2-py3-none-any.whl", hash = "sha256:28009937d8031054830160fce6d409ed342816b543597cece116d966c6d99e15", size = 22320 },
]

[[package]]
name = "jinxed"
version = "1.3.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "ansicon", marker = "platform_system == 'Windows'" },
]
sdist = { url = "https://files.pythonhosted.org/packages/20/d0/59b2b80e7a52d255f9e0ad040d2e826342d05580c4b1d7d7747cfb8db731/jinxed-1.3.0.tar.gz", hash = "sha256:1593124b18a41b7a3da3b078471442e51dbad3d77b4d4f2b0c26ab6f7d660dbf", size = 80981 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/27/e3/0e0014d6ab159d48189e92044ace13b1e1fe9aa3024ba9f4e8cf172aa7c2/jinxed-1.3.0-py2.py3-none-any.whl", hash = "sha256:b993189f39dc2d7504d802152671535b06d380b26d78070559551cbf92df4fc5", size = 33085 },
]

[[package]]
name = "log-symbols"
version = "0.0.14"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "colorama" },
]
sdist = { url = "https://files.pythonhosted.org/packages/45/87/e86645d758a4401c8c81914b6a88470634d1785c9ad09823fa4a1bd89250/log_symbols-0.0.14.tar.gz", hash = "sha256:cf0bbc6fe1a8e53f0d174a716bc625c4f87043cc21eb55dd8a740cfe22680556", size = 3211 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/28/5d/d710c38be68b0fb54e645048fe359c3904cc3cb64b2de9d40e1712bf110c/log_symbols-0.0.14-py3-none-any.whl", hash = "sha256:4952106ff8b605ab7d5081dd2c7e6ca7374584eff7086f499c06edd1ce56dcca", size = 3081 },
]

[[package]]
name = "markdown-it-py"
version = "3.0.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "mdurl" },
]
sdist = { url = "https://files.pythonhosted.org/packages/38/71/3b932df36c1a044d397a1f92d1cf91ee0a503d91e470cbd670aa66b07ed0/markdown-it-py-3.0.0.tar.gz", hash = "sha256:e3f60a94fa066dc52ec76661e37c851cb232d92f9886b15cb560aaada2df8feb", size = 74596 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/42/d7/1ec15b46af6af88f19b8e5ffea08fa375d433c998b8a7639e76935c14f1f/markdown_it_py-3.0.0-py3-none-any.whl", hash = "sha256:355216845c60bd96232cd8d8c40e8f9765cc86f46880e43a8fd22dc1a1a8cab1", size = 87528 },
]

[[package]]
name = "mdurl"
version = "0.1.2"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/d6/54/cfe61301667036ec958cb99bd3efefba235e65cdeb9c84d24a8293ba1d90/mdurl-0.1.2.tar.gz", hash = "sha256:bb413d29f5eea38f31dd4754dd7377d4465116fb207585f97bf925588687c1ba", size = 8729 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/b3/38/89ba8ad64ae25be8de66a6d463314cf1eb366222074cfda9ee839c56a4b4/mdurl-0.1.2-py3-none-any.whl", hash = "sha256:84008a41e51615a49fc9966191ff91509e3c40b939176e643fd50a5c2196b8f8", size = 9979 },
]

[[package]]
name = "multidict"
version = "6.1.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/d6/be/504b89a5e9ca731cd47487e91c469064f8ae5af93b7259758dcfc2b9c848/multidict-6.1.0.tar.gz", hash = "sha256:22ae2ebf9b0c69d206c003e2f6a914ea33f0a932d4aa16f236afc049d9958f4a", size = 64002 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/93/13/df3505a46d0cd08428e4c8169a196131d1b0c4b515c3649829258843dde6/multidict-6.1.0-cp311-cp311-macosx_10_9_universal2.whl", hash = "sha256:3efe2c2cb5763f2f1b275ad2bf7a287d3f7ebbef35648a9726e3b69284a4f3d6", size = 48570 },
    { url = "https://files.pythonhosted.org/packages/f0/e1/a215908bfae1343cdb72f805366592bdd60487b4232d039c437fe8f5013d/multidict-6.1.0-cp311-cp311-macosx_10_9_x86_64.whl", hash = "sha256:c7053d3b0353a8b9de430a4f4b4268ac9a4fb3481af37dfe49825bf45ca24156", size = 29316 },
    { url = "https://files.pythonhosted.org/packages/70/0f/6dc70ddf5d442702ed74f298d69977f904960b82368532c88e854b79f72b/multidict-6.1.0-cp311-cp311-macosx_11_0_arm64.whl", hash = "sha256:27e5fc84ccef8dfaabb09d82b7d179c7cf1a3fbc8a966f8274fcb4ab2eb4cadb", size = 29640 },
    { url = "https://files.pythonhosted.org/packages/d8/6d/9c87b73a13d1cdea30b321ef4b3824449866bd7f7127eceed066ccb9b9ff/multidict-6.1.0-cp311-cp311-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:0e2b90b43e696f25c62656389d32236e049568b39320e2735d51f08fd362761b", size = 131067 },
    { url = "https://files.pythonhosted.org/packages/cc/1e/1b34154fef373371fd6c65125b3d42ff5f56c7ccc6bfff91b9b3c60ae9e0/multidict-6.1.0-cp311-cp311-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:d83a047959d38a7ff552ff94be767b7fd79b831ad1cd9920662db05fec24fe72", size = 138507 },
    { url = "https://files.pythonhosted.org/packages/fb/e0/0bc6b2bac6e461822b5f575eae85da6aae76d0e2a79b6665d6206b8e2e48/multidict-6.1.0-cp311-cp311-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:d1a9dd711d0877a1ece3d2e4fea11a8e75741ca21954c919406b44e7cf971304", size = 133905 },
    { url = "https://files.pythonhosted.org/packages/ba/af/73d13b918071ff9b2205fcf773d316e0f8fefb4ec65354bbcf0b10908cc6/multidict-6.1.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:ec2abea24d98246b94913b76a125e855eb5c434f7c46546046372fe60f666351", size = 129004 },
    { url = "https://files.pythonhosted.org/packages/74/21/23960627b00ed39643302d81bcda44c9444ebcdc04ee5bedd0757513f259/multidict-6.1.0-cp311-cp311-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:4867cafcbc6585e4b678876c489b9273b13e9fff9f6d6d66add5e15d11d926cb", size = 121308 },
    { url = "https://files.pythonhosted.org/packages/8b/5c/cf282263ffce4a596ed0bb2aa1a1dddfe1996d6a62d08842a8d4b33dca13/multidict-6.1.0-cp311-cp311-musllinux_1_2_aarch64.whl", hash = "sha256:5b48204e8d955c47c55b72779802b219a39acc3ee3d0116d5080c388970b76e3", size = 132608 },
    { url = "https://files.pythonhosted.org/packages/d7/3e/97e778c041c72063f42b290888daff008d3ab1427f5b09b714f5a8eff294/multidict-6.1.0-cp311-cp311-musllinux_1_2_i686.whl", hash = "sha256:d8fff389528cad1618fb4b26b95550327495462cd745d879a8c7c2115248e399", size = 127029 },
    { url = "https://files.pythonhosted.org/packages/47/ac/3efb7bfe2f3aefcf8d103e9a7162572f01936155ab2f7ebcc7c255a23212/multidict-6.1.0-cp311-cp311-musllinux_1_2_ppc64le.whl", hash = "sha256:a7a9541cd308eed5e30318430a9c74d2132e9a8cb46b901326272d780bf2d423", size = 137594 },
    { url = "https://files.pythonhosted.org/packages/42/9b/6c6e9e8dc4f915fc90a9b7798c44a30773dea2995fdcb619870e705afe2b/multidict-6.1.0-cp311-cp311-musllinux_1_2_s390x.whl", hash = "sha256:da1758c76f50c39a2efd5e9859ce7d776317eb1dd34317c8152ac9251fc574a3", size = 134556 },
    { url = "https://files.pythonhosted.org/packages/1d/10/8e881743b26aaf718379a14ac58572a240e8293a1c9d68e1418fb11c0f90/multidict-6.1.0-cp311-cp311-musllinux_1_2_x86_64.whl", hash = "sha256:c943a53e9186688b45b323602298ab727d8865d8c9ee0b17f8d62d14b56f0753", size = 130993 },
    { url = "https://files.pythonhosted.org/packages/45/84/3eb91b4b557442802d058a7579e864b329968c8d0ea57d907e7023c677f2/multidict-6.1.0-cp311-cp311-win32.whl", hash = "sha256:90f8717cb649eea3504091e640a1b8568faad18bd4b9fcd692853a04475a4b80", size = 26405 },
    { url = "https://files.pythonhosted.org/packages/9f/0b/ad879847ecbf6d27e90a6eabb7eff6b62c129eefe617ea45eae7c1f0aead/multidict-6.1.0-cp311-cp311-win_amd64.whl", hash = "sha256:82176036e65644a6cc5bd619f65f6f19781e8ec2e5330f51aa9ada7504cc1926", size = 28795 },
    { url = "https://files.pythonhosted.org/packages/fd/16/92057c74ba3b96d5e211b553895cd6dc7cc4d1e43d9ab8fafc727681ef71/multidict-6.1.0-cp312-cp312-macosx_10_9_universal2.whl", hash = "sha256:b04772ed465fa3cc947db808fa306d79b43e896beb677a56fb2347ca1a49c1fa", size = 48713 },
    { url = "https://files.pythonhosted.org/packages/94/3d/37d1b8893ae79716179540b89fc6a0ee56b4a65fcc0d63535c6f5d96f217/multidict-6.1.0-cp312-cp312-macosx_10_9_x86_64.whl", hash = "sha256:6180c0ae073bddeb5a97a38c03f30c233e0a4d39cd86166251617d1bbd0af436", size = 29516 },
    { url = "https://files.pythonhosted.org/packages/a2/12/adb6b3200c363062f805275b4c1e656be2b3681aada66c80129932ff0bae/multidict-6.1.0-cp312-cp312-macosx_11_0_arm64.whl", hash = "sha256:071120490b47aa997cca00666923a83f02c7fbb44f71cf7f136df753f7fa8761", size = 29557 },
    { url = "https://files.pythonhosted.org/packages/47/e9/604bb05e6e5bce1e6a5cf80a474e0f072e80d8ac105f1b994a53e0b28c42/multidict-6.1.0-cp312-cp312-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:50b3a2710631848991d0bf7de077502e8994c804bb805aeb2925a981de58ec2e", size = 130170 },
    { url = "https://files.pythonhosted.org/packages/7e/13/9efa50801785eccbf7086b3c83b71a4fb501a4d43549c2f2f80b8787d69f/multidict-6.1.0-cp312-cp312-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:b58c621844d55e71c1b7f7c498ce5aa6985d743a1a59034c57a905b3f153c1ef", size = 134836 },
    { url = "https://files.pythonhosted.org/packages/bf/0f/93808b765192780d117814a6dfcc2e75de6dcc610009ad408b8814dca3ba/multidict-6.1.0-cp312-cp312-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:55b6d90641869892caa9ca42ff913f7ff1c5ece06474fbd32fb2cf6834726c95", size = 133475 },
    { url = "https://files.pythonhosted.org/packages/d3/c8/529101d7176fe7dfe1d99604e48d69c5dfdcadb4f06561f465c8ef12b4df/multidict-6.1.0-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:4b820514bfc0b98a30e3d85462084779900347e4d49267f747ff54060cc33925", size = 131049 },
    { url = "https://files.pythonhosted.org/packages/ca/0c/fc85b439014d5a58063e19c3a158a889deec399d47b5269a0f3b6a2e28bc/multidict-6.1.0-cp312-cp312-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:10a9b09aba0c5b48c53761b7c720aaaf7cf236d5fe394cd399c7ba662d5f9966", size = 120370 },
    { url = "https://files.pythonhosted.org/packages/db/46/d4416eb20176492d2258fbd47b4abe729ff3b6e9c829ea4236f93c865089/multidict-6.1.0-cp312-cp312-musllinux_1_2_aarch64.whl", hash = "sha256:1e16bf3e5fc9f44632affb159d30a437bfe286ce9e02754759be5536b169b305", size = 125178 },
    { url = "https://files.pythonhosted.org/packages/5b/46/73697ad7ec521df7de5531a32780bbfd908ded0643cbe457f981a701457c/multidict-6.1.0-cp312-cp312-musllinux_1_2_i686.whl", hash = "sha256:76f364861c3bfc98cbbcbd402d83454ed9e01a5224bb3a28bf70002a230f73e2", size = 119567 },
    { url = "https://files.pythonhosted.org/packages/cd/ed/51f060e2cb0e7635329fa6ff930aa5cffa17f4c7f5c6c3ddc3500708e2f2/multidict-6.1.0-cp312-cp312-musllinux_1_2_ppc64le.whl", hash = "sha256:820c661588bd01a0aa62a1283f20d2be4281b086f80dad9e955e690c75fb54a2", size = 129822 },
    { url = "https://files.pythonhosted.org/packages/df/9e/ee7d1954b1331da3eddea0c4e08d9142da5f14b1321c7301f5014f49d492/multidict-6.1.0-cp312-cp312-musllinux_1_2_s390x.whl", hash = "sha256:0e5f362e895bc5b9e67fe6e4ded2492d8124bdf817827f33c5b46c2fe3ffaca6", size = 128656 },
    { url = "https://files.pythonhosted.org/packages/77/00/8538f11e3356b5d95fa4b024aa566cde7a38aa7a5f08f4912b32a037c5dc/multidict-6.1.0-cp312-cp312-musllinux_1_2_x86_64.whl", hash = "sha256:3ec660d19bbc671e3a6443325f07263be452c453ac9e512f5eb935e7d4ac28b3", size = 125360 },
    { url = "https://files.pythonhosted.org/packages/be/05/5d334c1f2462d43fec2363cd00b1c44c93a78c3925d952e9a71caf662e96/multidict-6.1.0-cp312-cp312-win32.whl", hash = "sha256:58130ecf8f7b8112cdb841486404f1282b9c86ccb30d3519faf301b2e5659133", size = 26382 },
    { url = "https://files.pythonhosted.org/packages/a3/bf/f332a13486b1ed0496d624bcc7e8357bb8053823e8cd4b9a18edc1d97e73/multidict-6.1.0-cp312-cp312-win_amd64.whl", hash = "sha256:188215fc0aafb8e03341995e7c4797860181562380f81ed0a87ff455b70bf1f1", size = 28529 },
    { url = "https://files.pythonhosted.org/packages/99/b7/b9e70fde2c0f0c9af4cc5277782a89b66d35948ea3369ec9f598358c3ac5/multidict-6.1.0-py3-none-any.whl", hash = "sha256:48e171e52d1c4d33888e529b999e5900356b9ae588c2f09a52dcefb158b27506", size = 10051 },
]

[[package]]
name = "mutagen"
version = "1.47.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/81/e6/64bc71b74eef4b68e61eb921dcf72dabd9e4ec4af1e11891bbd312ccbb77/mutagen-1.47.0.tar.gz", hash = "sha256:719fadef0a978c31b4cf3c956261b3c58b6948b32023078a2117b1de09f0fc99", size = 1274186 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/b0/7a/620f945b96be1f6ee357d211d5bf74ab1b7fe72a9f1525aafbfe3aee6875/mutagen-1.47.0-py3-none-any.whl", hash = "sha256:edd96f50c5907a9539d8e5bba7245f62c9f520aef333d13392a79a4f70aca719", size = 194391 },
]

[[package]]
name = "mypy"
version = "1.13.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "mypy-extensions" },
    { name = "typing-extensions" },
]
sdist = { url = "https://files.pythonhosted.org/packages/e8/21/7e9e523537991d145ab8a0a2fd98548d67646dc2aaaf6091c31ad883e7c1/mypy-1.13.0.tar.gz", hash = "sha256:0291a61b6fbf3e6673e3405cfcc0e7650bebc7939659fdca2702958038bd835e", size = 3152532 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/d0/19/de0822609e5b93d02579075248c7aa6ceaddcea92f00bf4ea8e4c22e3598/mypy-1.13.0-cp311-cp311-macosx_10_9_x86_64.whl", hash = "sha256:581665e6f3a8a9078f28d5502f4c334c0c8d802ef55ea0e7276a6e409bc0d82d", size = 10939027 },
    { url = "https://files.pythonhosted.org/packages/c8/71/6950fcc6ca84179137e4cbf7cf41e6b68b4a339a1f5d3e954f8c34e02d66/mypy-1.13.0-cp311-cp311-macosx_11_0_arm64.whl", hash = "sha256:3ddb5b9bf82e05cc9a627e84707b528e5c7caaa1c55c69e175abb15a761cec2d", size = 10108699 },
    { url = "https://files.pythonhosted.org/packages/26/50/29d3e7dd166e74dc13d46050b23f7d6d7533acf48f5217663a3719db024e/mypy-1.13.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.manylinux_2_28_x86_64.whl", hash = "sha256:20c7ee0bc0d5a9595c46f38beb04201f2620065a93755704e141fcac9f59db2b", size = 12506263 },
    { url = "https://files.pythonhosted.org/packages/3f/1d/676e76f07f7d5ddcd4227af3938a9c9640f293b7d8a44dd4ff41d4db25c1/mypy-1.13.0-cp311-cp311-musllinux_1_1_x86_64.whl", hash = "sha256:3790ded76f0b34bc9c8ba4def8f919dd6a46db0f5a6610fb994fe8efdd447f73", size = 12984688 },
    { url = "https://files.pythonhosted.org/packages/9c/03/5a85a30ae5407b1d28fab51bd3e2103e52ad0918d1e68f02a7778669a307/mypy-1.13.0-cp311-cp311-win_amd64.whl", hash = "sha256:51f869f4b6b538229c1d1bcc1dd7d119817206e2bc54e8e374b3dfa202defcca", size = 9626811 },
    { url = "https://files.pythonhosted.org/packages/fb/31/c526a7bd2e5c710ae47717c7a5f53f616db6d9097caf48ad650581e81748/mypy-1.13.0-cp312-cp312-macosx_10_13_x86_64.whl", hash = "sha256:5c7051a3461ae84dfb5dd15eff5094640c61c5f22257c8b766794e6dd85e72d5", size = 11077900 },
    { url = "https://files.pythonhosted.org/packages/83/67/b7419c6b503679d10bd26fc67529bc6a1f7a5f220bbb9f292dc10d33352f/mypy-1.13.0-cp312-cp312-macosx_11_0_arm64.whl", hash = "sha256:39bb21c69a5d6342f4ce526e4584bc5c197fd20a60d14a8624d8743fffb9472e", size = 10074818 },
    { url = "https://files.pythonhosted.org/packages/ba/07/37d67048786ae84e6612575e173d713c9a05d0ae495dde1e68d972207d98/mypy-1.13.0-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.manylinux_2_28_x86_64.whl", hash = "sha256:164f28cb9d6367439031f4c81e84d3ccaa1e19232d9d05d37cb0bd880d3f93c2", size = 12589275 },
    { url = "https://files.pythonhosted.org/packages/1f/17/b1018c6bb3e9f1ce3956722b3bf91bff86c1cefccca71cec05eae49d6d41/mypy-1.13.0-cp312-cp312-musllinux_1_1_x86_64.whl", hash = "sha256:a4c1bfcdbce96ff5d96fc9b08e3831acb30dc44ab02671eca5953eadad07d6d0", size = 13037783 },
    { url = "https://files.pythonhosted.org/packages/cb/32/cd540755579e54a88099aee0287086d996f5a24281a673f78a0e14dba150/mypy-1.13.0-cp312-cp312-win_amd64.whl", hash = "sha256:a0affb3a79a256b4183ba09811e3577c5163ed06685e4d4b46429a271ba174d2", size = 9726197 },
    { url = "https://files.pythonhosted.org/packages/3b/86/72ce7f57431d87a7ff17d442f521146a6585019eb8f4f31b7c02801f78ad/mypy-1.13.0-py3-none-any.whl", hash = "sha256:9c250883f9fd81d212e0952c92dbfcc96fc237f4b7c92f56ac81fd48460b3e5a", size = 2647043 },
]

[[package]]
name = "mypy-extensions"
version = "1.0.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/98/a4/1ab47638b92648243faf97a5aeb6ea83059cc3624972ab6b8d2316078d3f/mypy_extensions-1.0.0.tar.gz", hash = "sha256:75dbf8955dc00442a438fc4d0666508a9a97b6bd41aa2f0ffe9d2f2725af0782", size = 4433 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/2a/e2/5d3f6ada4297caebe1a2add3b126fe800c96f56dbe5d1988a2cbe0b267aa/mypy_extensions-1.0.0-py3-none-any.whl", hash = "sha256:4392f6c0eb8a5668a69e23d168ffa70f0be9ccfd32b5cc2d26a34ae5b844552d", size = 4695 },
]

[[package]]
name = "natsort"
version = "8.4.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/e2/a9/a0c57aee75f77794adaf35322f8b6404cbd0f89ad45c87197a937764b7d0/natsort-8.4.0.tar.gz", hash = "sha256:45312c4a0e5507593da193dedd04abb1469253b601ecaf63445ad80f0a1ea581", size = 76575 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/ef/82/7a9d0550484a62c6da82858ee9419f3dd1ccc9aa1c26a1e43da3ecd20b0d/natsort-8.4.0-py3-none-any.whl", hash = "sha256:4732914fb471f56b5cce04d7bae6f164a592c7712e1c85f9ef585e197299521c", size = 38268 },
]

[[package]]
name = "numpy"
version = "2.1.2"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/4b/d1/8a730ea07f4a37d94f9172f4ce1d81064b7a64766b460378be278952de75/numpy-2.1.2.tar.gz", hash = "sha256:13532a088217fa624c99b843eeb54640de23b3414b14aa66d023805eb731066c", size = 18878063 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/aa/9c/9a6ec3ae89cd0648d419781284308f2956d2a61d932b5ac9682c956a171b/numpy-2.1.2-cp311-cp311-macosx_10_9_x86_64.whl", hash = "sha256:b42a1a511c81cc78cbc4539675713bbcf9d9c3913386243ceff0e9429ca892fe", size = 21154845 },
    { url = "https://files.pythonhosted.org/packages/02/69/9f05c4ecc75fabf297b17743996371b4c3dfc4d92e15c5c38d8bb3db8d74/numpy-2.1.2-cp311-cp311-macosx_11_0_arm64.whl", hash = "sha256:faa88bc527d0f097abdc2c663cddf37c05a1c2f113716601555249805cf573f1", size = 13789409 },
    { url = "https://files.pythonhosted.org/packages/34/4e/f95c99217bf77bbfaaf660d693c10bd0dc03b6032d19316d316088c9e479/numpy-2.1.2-cp311-cp311-macosx_14_0_arm64.whl", hash = "sha256:c82af4b2ddd2ee72d1fc0c6695048d457e00b3582ccde72d8a1c991b808bb20f", size = 5352097 },
    { url = "https://files.pythonhosted.org/packages/06/13/f5d87a497c16658e9af8920449b0b5692b469586b8231340c672962071c5/numpy-2.1.2-cp311-cp311-macosx_14_0_x86_64.whl", hash = "sha256:13602b3174432a35b16c4cfb5de9a12d229727c3dd47a6ce35111f2ebdf66ff4", size = 6891195 },
    { url = "https://files.pythonhosted.org/packages/6c/89/691ac07429ac061b344d5e37fa8e94be51a6017734aea15f2d9d7c6d119a/numpy-2.1.2-cp311-cp311-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:1ebec5fd716c5a5b3d8dfcc439be82a8407b7b24b230d0ad28a81b61c2f4659a", size = 13895153 },
    { url = "https://files.pythonhosted.org/packages/23/69/538317f0d925095537745f12aced33be1570bbdc4acde49b33748669af96/numpy-2.1.2-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:e2b49c3c0804e8ecb05d59af8386ec2f74877f7ca8fd9c1e00be2672e4d399b1", size = 16338306 },
    { url = "https://files.pythonhosted.org/packages/af/03/863fe7062c2106d3c151f7df9353f2ae2237c1dd6900f127a3eb1f24cb1b/numpy-2.1.2-cp311-cp311-musllinux_1_1_x86_64.whl", hash = "sha256:2cbba4b30bf31ddbe97f1c7205ef976909a93a66bb1583e983adbd155ba72ac2", size = 16710893 },
    { url = "https://files.pythonhosted.org/packages/70/77/0ad9efe25482009873f9660d29a40a8c41a6f0e8b541195e3c95c70684c5/numpy-2.1.2-cp311-cp311-musllinux_1_2_aarch64.whl", hash = "sha256:8e00ea6fc82e8a804433d3e9cedaa1051a1422cb6e443011590c14d2dea59146", size = 14398048 },
    { url = "https://files.pythonhosted.org/packages/3e/0f/e785fe75544db9f2b0bb1c181e13ceff349ce49753d807fd9672916aa06d/numpy-2.1.2-cp311-cp311-win32.whl", hash = "sha256:5006b13a06e0b38d561fab5ccc37581f23c9511879be7693bd33c7cd15ca227c", size = 6533458 },
    { url = "https://files.pythonhosted.org/packages/d4/96/450054662295125af861d48d2c4bc081dadcf1974a879b2104613157aa62/numpy-2.1.2-cp311-cp311-win_amd64.whl", hash = "sha256:f1eb068ead09f4994dec71c24b2844f1e4e4e013b9629f812f292f04bd1510d9", size = 12870896 },
    { url = "https://files.pythonhosted.org/packages/a0/7d/554a6838f37f3ada5a55f25173c619d556ae98092a6e01afb6e710501d70/numpy-2.1.2-cp312-cp312-macosx_10_13_x86_64.whl", hash = "sha256:d7bf0a4f9f15b32b5ba53147369e94296f5fffb783db5aacc1be15b4bf72f43b", size = 20848077 },
    { url = "https://files.pythonhosted.org/packages/b0/29/cb48a402ea879e645b16218718f3f7d9588a77d674a9dcf22e4c43487636/numpy-2.1.2-cp312-cp312-macosx_11_0_arm64.whl", hash = "sha256:b1d0fcae4f0949f215d4632be684a539859b295e2d0cb14f78ec231915d644db", size = 13493242 },
    { url = "https://files.pythonhosted.org/packages/56/44/f899b0581766c230da42f751b7b8896d096640b19b312164c267e48d36cb/numpy-2.1.2-cp312-cp312-macosx_14_0_arm64.whl", hash = "sha256:f751ed0a2f250541e19dfca9f1eafa31a392c71c832b6bb9e113b10d050cb0f1", size = 5089219 },
    { url = "https://files.pythonhosted.org/packages/79/8f/b987070d45161a7a4504afc67ed38544ed2c0ed5576263599a0402204a9c/numpy-2.1.2-cp312-cp312-macosx_14_0_x86_64.whl", hash = "sha256:bd33f82e95ba7ad632bc57837ee99dba3d7e006536200c4e9124089e1bf42426", size = 6620167 },
    { url = "https://files.pythonhosted.org/packages/c4/a7/af3329fda3c3ec31d9b650e42bbcd3422fc62a765cbb1405fde4177a0996/numpy-2.1.2-cp312-cp312-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:1b8cde4f11f0a975d1fd59373b32e2f5a562ade7cde4f85b7137f3de8fbb29a0", size = 13604905 },
    { url = "https://files.pythonhosted.org/packages/9b/b4/e3c7e6fab0f77fff6194afa173d1f2342073d91b1d3b4b30b17c3fb4407a/numpy-2.1.2-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:6d95f286b8244b3649b477ac066c6906fbb2905f8ac19b170e2175d3d799f4df", size = 16041825 },
    { url = "https://files.pythonhosted.org/packages/e9/50/6828e66a78aa03147c111f84d55f33ce2dde547cb578d6744a3b06a0124b/numpy-2.1.2-cp312-cp312-musllinux_1_1_x86_64.whl", hash = "sha256:ab4754d432e3ac42d33a269c8567413bdb541689b02d93788af4131018cbf366", size = 16409541 },
    { url = "https://files.pythonhosted.org/packages/bf/72/66af7916d9c3c6dbfbc8acdd4930c65461e1953374a2bc43d00f948f004a/numpy-2.1.2-cp312-cp312-musllinux_1_2_aarch64.whl", hash = "sha256:e585c8ae871fd38ac50598f4763d73ec5497b0de9a0ab4ef5b69f01c6a046142", size = 14081134 },
    { url = "https://files.pythonhosted.org/packages/dc/5a/59a67d84f33fe00ae74f0b5b69dd4f93a586a4aba7f7e19b54b2133db038/numpy-2.1.2-cp312-cp312-win32.whl", hash = "sha256:9c6c754df29ce6a89ed23afb25550d1c2d5fdb9901d9c67a16e0b16eaf7e2550", size = 6237784 },
    { url = "https://files.pythonhosted.org/packages/4c/79/73735a6a5dad6059c085f240a4e74c9270feccd2bc66e4d31b5ca01d329c/numpy-2.1.2-cp312-cp312-win_amd64.whl", hash = "sha256:456e3b11cb79ac9946c822a56346ec80275eaf2950314b249b512896c0d2505e", size = 12568254 },
]

[[package]]
name = "paramiko"
version = "3.5.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "bcrypt" },
    { name = "cryptography" },
    { name = "pynacl" },
]
sdist = { url = "https://files.pythonhosted.org/packages/1b/0f/c00296e36ff7485935b83d466c4f2cf5934b84b0ad14e81796e1d9d3609b/paramiko-3.5.0.tar.gz", hash = "sha256:ad11e540da4f55cedda52931f1a3f812a8238a7af7f62a60de538cd80bb28124", size = 1704305 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/1f/66/14b2c030fcce69cba482d205c2d1462ca5c77303a263260dcb1192801c85/paramiko-3.5.0-py3-none-any.whl", hash = "sha256:1fedf06b085359051cd7d0d270cebe19e755a8a921cc2ddbfa647fb0cd7d68f9", size = 227143 },
]

[[package]]
name = "path"
version = "17.0.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/ff/a3/5dac44ce60ad6543578736a5729c5c2130cdac1c3117c61aad0583c2e3c6/path-17.0.0.tar.gz", hash = "sha256:e1540261d22df1416fb1b498b3b1ed5353a371a48fe197d66611bb01e7fab2d5", size = 49721 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/55/49/5ffc63f96029e4f899d6caee9db40c445ded1bf15cb60b32d77363c2c8de/path-17.0.0-py3-none-any.whl", hash = "sha256:b7309739c569e30110a34c6c812e582c09ff504c43e1232817410181838918ed", size = 24831 },
]

[[package]]
name = "path-py"
version = "12.5.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "path" },
]
sdist = { url = "https://files.pythonhosted.org/packages/b6/e3/81be70016d58ade0f516191fa80152daba5453d0b07ce648d9daae86a188/path.py-12.5.0.tar.gz", hash = "sha256:8d885e8b2497aed005703d94e0fd97943401f035e42a136810308bff034529a8", size = 15713 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/8f/04/130b7a538c25693c85c4dee7e25d126ebf5511b1eb7320e64906687b159e/path.py-12.5.0-py3-none-any.whl", hash = "sha256:a43e82eb2c344c3fd0b9d6352f6b856f40b8b7d3d65cc05978b42c3715668496", size = 2251 },
]

[[package]]
name = "pathlib"
version = "1.0.1"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/ac/aa/9b065a76b9af472437a0059f77e8f962fe350438b927cb80184c32f075eb/pathlib-1.0.1.tar.gz", hash = "sha256:6940718dfc3eff4258203ad5021090933e5c04707d5ca8cc9e73c94a7894ea9f", size = 49298 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/78/f9/690a8600b93c332de3ab4a344a4ac34f00c8f104917061f779db6a918ed6/pathlib-1.0.1-py3-none-any.whl", hash = "sha256:f35f95ab8b0f59e6d354090350b44a80a80635d22efdedfa84c7ad1cf0a74147", size = 14363 },
]

[[package]]
name = "pexpect"
version = "4.9.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "ptyprocess" },
]
sdist = { url = "https://files.pythonhosted.org/packages/42/92/cc564bf6381ff43ce1f4d06852fc19a2f11d180f23dc32d9588bee2f149d/pexpect-4.9.0.tar.gz", hash = "sha256:ee7d41123f3c9911050ea2c2dac107568dc43b2d3b0c7557a33212c398ead30f", size = 166450 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/9e/c3/059298687310d527a58bb01f3b1965787ee3b40dce76752eda8b44e9a2c5/pexpect-4.9.0-py2.py3-none-any.whl", hash = "sha256:7236d1e080e4936be2dc3e326cec0af72acf9212a7e1d060210e70a47e253523", size = 63772 },
]

[[package]]
name = "pillow"
version = "11.0.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/a5/26/0d95c04c868f6bdb0c447e3ee2de5564411845e36a858cfd63766bc7b563/pillow-11.0.0.tar.gz", hash = "sha256:72bacbaf24ac003fea9bff9837d1eedb6088758d41e100c1552930151f677739", size = 46737780 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/f0/eb/f7e21b113dd48a9c97d364e0915b3988c6a0b6207652f5a92372871b7aa4/pillow-11.0.0-cp311-cp311-macosx_10_10_x86_64.whl", hash = "sha256:1c1d72714f429a521d8d2d018badc42414c3077eb187a59579f28e4270b4b0fc", size = 3154705 },
    { url = "https://files.pythonhosted.org/packages/25/b3/2b54a1d541accebe6bd8b1358b34ceb2c509f51cb7dcda8687362490da5b/pillow-11.0.0-cp311-cp311-macosx_11_0_arm64.whl", hash = "sha256:499c3a1b0d6fc8213519e193796eb1a86a1be4b1877d678b30f83fd979811d1a", size = 2979222 },
    { url = "https://files.pythonhosted.org/packages/20/12/1a41eddad8265c5c19dda8fb6c269ce15ee25e0b9f8f26286e6202df6693/pillow-11.0.0-cp311-cp311-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:c8b2351c85d855293a299038e1f89db92a2f35e8d2f783489c6f0b2b5f3fe8a3", size = 4190220 },
    { url = "https://files.pythonhosted.org/packages/a9/9b/8a8c4d07d77447b7457164b861d18f5a31ae6418ef5c07f6f878fa09039a/pillow-11.0.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:6f4dba50cfa56f910241eb7f883c20f1e7b1d8f7d91c750cd0b318bad443f4d5", size = 4291399 },
    { url = "https://files.pythonhosted.org/packages/fc/e4/130c5fab4a54d3991129800dd2801feeb4b118d7630148cd67f0e6269d4c/pillow-11.0.0-cp311-cp311-manylinux_2_28_aarch64.whl", hash = "sha256:5ddbfd761ee00c12ee1be86c9c0683ecf5bb14c9772ddbd782085779a63dd55b", size = 4202709 },
    { url = "https://files.pythonhosted.org/packages/39/63/b3fc299528d7df1f678b0666002b37affe6b8751225c3d9c12cf530e73ed/pillow-11.0.0-cp311-cp311-manylinux_2_28_x86_64.whl", hash = "sha256:45c566eb10b8967d71bf1ab8e4a525e5a93519e29ea071459ce517f6b903d7fa", size = 4372556 },
    { url = "https://files.pythonhosted.org/packages/c6/a6/694122c55b855b586c26c694937d36bb8d3b09c735ff41b2f315c6e66a10/pillow-11.0.0-cp311-cp311-musllinux_1_2_aarch64.whl", hash = "sha256:b4fd7bd29610a83a8c9b564d457cf5bd92b4e11e79a4ee4716a63c959699b306", size = 4287187 },
    { url = "https://files.pythonhosted.org/packages/ba/a9/f9d763e2671a8acd53d29b1e284ca298bc10a595527f6be30233cdb9659d/pillow-11.0.0-cp311-cp311-musllinux_1_2_x86_64.whl", hash = "sha256:cb929ca942d0ec4fac404cbf520ee6cac37bf35be479b970c4ffadf2b6a1cad9", size = 4418468 },
    { url = "https://files.pythonhosted.org/packages/6e/0e/b5cbad2621377f11313a94aeb44ca55a9639adabcaaa073597a1925f8c26/pillow-11.0.0-cp311-cp311-win32.whl", hash = "sha256:006bcdd307cc47ba43e924099a038cbf9591062e6c50e570819743f5607404f5", size = 2249249 },
    { url = "https://files.pythonhosted.org/packages/dc/83/1470c220a4ff06cd75fc609068f6605e567ea51df70557555c2ab6516b2c/pillow-11.0.0-cp311-cp311-win_amd64.whl", hash = "sha256:52a2d8323a465f84faaba5236567d212c3668f2ab53e1c74c15583cf507a0291", size = 2566769 },
    { url = "https://files.pythonhosted.org/packages/52/98/def78c3a23acee2bcdb2e52005fb2810ed54305602ec1bfcfab2bda6f49f/pillow-11.0.0-cp311-cp311-win_arm64.whl", hash = "sha256:16095692a253047fe3ec028e951fa4221a1f3ed3d80c397e83541a3037ff67c9", size = 2254611 },
    { url = "https://files.pythonhosted.org/packages/1c/a3/26e606ff0b2daaf120543e537311fa3ae2eb6bf061490e4fea51771540be/pillow-11.0.0-cp312-cp312-macosx_10_13_x86_64.whl", hash = "sha256:d2c0a187a92a1cb5ef2c8ed5412dd8d4334272617f532d4ad4de31e0495bd923", size = 3147642 },
    { url = "https://files.pythonhosted.org/packages/4f/d5/1caabedd8863526a6cfa44ee7a833bd97f945dc1d56824d6d76e11731939/pillow-11.0.0-cp312-cp312-macosx_11_0_arm64.whl", hash = "sha256:084a07ef0821cfe4858fe86652fffac8e187b6ae677e9906e192aafcc1b69903", size = 2978999 },
    { url = "https://files.pythonhosted.org/packages/d9/ff/5a45000826a1aa1ac6874b3ec5a856474821a1b59d838c4f6ce2ee518fe9/pillow-11.0.0-cp312-cp312-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:8069c5179902dcdce0be9bfc8235347fdbac249d23bd90514b7a47a72d9fecf4", size = 4196794 },
    { url = "https://files.pythonhosted.org/packages/9d/21/84c9f287d17180f26263b5f5c8fb201de0f88b1afddf8a2597a5c9fe787f/pillow-11.0.0-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:f02541ef64077f22bf4924f225c0fd1248c168f86e4b7abdedd87d6ebaceab0f", size = 4300762 },
    { url = "https://files.pythonhosted.org/packages/84/39/63fb87cd07cc541438b448b1fed467c4d687ad18aa786a7f8e67b255d1aa/pillow-11.0.0-cp312-cp312-manylinux_2_28_aarch64.whl", hash = "sha256:fcb4621042ac4b7865c179bb972ed0da0218a076dc1820ffc48b1d74c1e37fe9", size = 4210468 },
    { url = "https://files.pythonhosted.org/packages/7f/42/6e0f2c2d5c60f499aa29be14f860dd4539de322cd8fb84ee01553493fb4d/pillow-11.0.0-cp312-cp312-manylinux_2_28_x86_64.whl", hash = "sha256:00177a63030d612148e659b55ba99527803288cea7c75fb05766ab7981a8c1b7", size = 4381824 },
    { url = "https://files.pythonhosted.org/packages/31/69/1ef0fb9d2f8d2d114db982b78ca4eeb9db9a29f7477821e160b8c1253f67/pillow-11.0.0-cp312-cp312-musllinux_1_2_aarch64.whl", hash = "sha256:8853a3bf12afddfdf15f57c4b02d7ded92c7a75a5d7331d19f4f9572a89c17e6", size = 4296436 },
    { url = "https://files.pythonhosted.org/packages/44/ea/dad2818c675c44f6012289a7c4f46068c548768bc6c7f4e8c4ae5bbbc811/pillow-11.0.0-cp312-cp312-musllinux_1_2_x86_64.whl", hash = "sha256:3107c66e43bda25359d5ef446f59c497de2b5ed4c7fdba0894f8d6cf3822dafc", size = 4429714 },
    { url = "https://files.pythonhosted.org/packages/af/3a/da80224a6eb15bba7a0dcb2346e2b686bb9bf98378c0b4353cd88e62b171/pillow-11.0.0-cp312-cp312-win32.whl", hash = "sha256:86510e3f5eca0ab87429dd77fafc04693195eec7fd6a137c389c3eeb4cfb77c6", size = 2249631 },
    { url = "https://files.pythonhosted.org/packages/57/97/73f756c338c1d86bb802ee88c3cab015ad7ce4b838f8a24f16b676b1ac7c/pillow-11.0.0-cp312-cp312-win_amd64.whl", hash = "sha256:8ec4a89295cd6cd4d1058a5e6aec6bf51e0eaaf9714774e1bfac7cfc9051db47", size = 2567533 },
    { url = "https://files.pythonhosted.org/packages/0b/30/2b61876e2722374558b871dfbfcbe4e406626d63f4f6ed92e9c8e24cac37/pillow-11.0.0-cp312-cp312-win_arm64.whl", hash = "sha256:27a7860107500d813fcd203b4ea19b04babe79448268403172782754870dac25", size = 2254890 },
]

[[package]]
name = "propcache"
version = "0.2.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/a9/4d/5e5a60b78dbc1d464f8a7bbaeb30957257afdc8512cbb9dfd5659304f5cd/propcache-0.2.0.tar.gz", hash = "sha256:df81779732feb9d01e5d513fad0122efb3d53bbc75f61b2a4f29a020bc985e70", size = 40951 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/e0/1c/71eec730e12aec6511e702ad0cd73c2872eccb7cad39de8ba3ba9de693ef/propcache-0.2.0-cp311-cp311-macosx_10_9_universal2.whl", hash = "sha256:63f13bf09cc3336eb04a837490b8f332e0db41da66995c9fd1ba04552e516354", size = 80811 },
    { url = "https://files.pythonhosted.org/packages/89/c3/7e94009f9a4934c48a371632197406a8860b9f08e3f7f7d922ab69e57a41/propcache-0.2.0-cp311-cp311-macosx_10_9_x86_64.whl", hash = "sha256:608cce1da6f2672a56b24a015b42db4ac612ee709f3d29f27a00c943d9e851de", size = 46365 },
    { url = "https://files.pythonhosted.org/packages/c0/1d/c700d16d1d6903aeab28372fe9999762f074b80b96a0ccc953175b858743/propcache-0.2.0-cp311-cp311-macosx_11_0_arm64.whl", hash = "sha256:466c219deee4536fbc83c08d09115249db301550625c7fef1c5563a584c9bc87", size = 45602 },
    { url = "https://files.pythonhosted.org/packages/2e/5e/4a3e96380805bf742712e39a4534689f4cddf5fa2d3a93f22e9fd8001b23/propcache-0.2.0-cp311-cp311-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:fc2db02409338bf36590aa985a461b2c96fce91f8e7e0f14c50c5fcc4f229016", size = 236161 },
    { url = "https://files.pythonhosted.org/packages/a5/85/90132481183d1436dff6e29f4fa81b891afb6cb89a7306f32ac500a25932/propcache-0.2.0-cp311-cp311-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:a6ed8db0a556343d566a5c124ee483ae113acc9a557a807d439bcecc44e7dfbb", size = 244938 },
    { url = "https://files.pythonhosted.org/packages/4a/89/c893533cb45c79c970834274e2d0f6d64383ec740be631b6a0a1d2b4ddc0/propcache-0.2.0-cp311-cp311-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:91997d9cb4a325b60d4e3f20967f8eb08dfcb32b22554d5ef78e6fd1dda743a2", size = 243576 },
    { url = "https://files.pythonhosted.org/packages/8c/56/98c2054c8526331a05f205bf45cbb2cda4e58e56df70e76d6a509e5d6ec6/propcache-0.2.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:4c7dde9e533c0a49d802b4f3f218fa9ad0a1ce21f2c2eb80d5216565202acab4", size = 236011 },
    { url = "https://files.pythonhosted.org/packages/2d/0c/8b8b9f8a6e1abd869c0fa79b907228e7abb966919047d294ef5df0d136cf/propcache-0.2.0-cp311-cp311-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:ffcad6c564fe6b9b8916c1aefbb37a362deebf9394bd2974e9d84232e3e08504", size = 224834 },
    { url = "https://files.pythonhosted.org/packages/18/bb/397d05a7298b7711b90e13108db697732325cafdcd8484c894885c1bf109/propcache-0.2.0-cp311-cp311-musllinux_1_2_aarch64.whl", hash = "sha256:97a58a28bcf63284e8b4d7b460cbee1edaab24634e82059c7b8c09e65284f178", size = 224946 },
    { url = "https://files.pythonhosted.org/packages/25/19/4fc08dac19297ac58135c03770b42377be211622fd0147f015f78d47cd31/propcache-0.2.0-cp311-cp311-musllinux_1_2_armv7l.whl", hash = "sha256:945db8ee295d3af9dbdbb698cce9bbc5c59b5c3fe328bbc4387f59a8a35f998d", size = 217280 },
    { url = "https://files.pythonhosted.org/packages/7e/76/c79276a43df2096ce2aba07ce47576832b1174c0c480fe6b04bd70120e59/propcache-0.2.0-cp311-cp311-musllinux_1_2_i686.whl", hash = "sha256:39e104da444a34830751715f45ef9fc537475ba21b7f1f5b0f4d71a3b60d7fe2", size = 220088 },
    { url = "https://files.pythonhosted.org/packages/c3/9a/8a8cf428a91b1336b883f09c8b884e1734c87f724d74b917129a24fe2093/propcache-0.2.0-cp311-cp311-musllinux_1_2_ppc64le.whl", hash = "sha256:c5ecca8f9bab618340c8e848d340baf68bcd8ad90a8ecd7a4524a81c1764b3db", size = 233008 },
    { url = "https://files.pythonhosted.org/packages/25/7b/768a8969abd447d5f0f3333df85c6a5d94982a1bc9a89c53c154bf7a8b11/propcache-0.2.0-cp311-cp311-musllinux_1_2_s390x.whl", hash = "sha256:c436130cc779806bdf5d5fae0d848713105472b8566b75ff70048c47d3961c5b", size = 237719 },
    { url = "https://files.pythonhosted.org/packages/ed/0d/e5d68ccc7976ef8b57d80613ac07bbaf0614d43f4750cf953f0168ef114f/propcache-0.2.0-cp311-cp311-musllinux_1_2_x86_64.whl", hash = "sha256:191db28dc6dcd29d1a3e063c3be0b40688ed76434622c53a284e5427565bbd9b", size = 227729 },
    { url = "https://files.pythonhosted.org/packages/05/64/17eb2796e2d1c3d0c431dc5f40078d7282f4645af0bb4da9097fbb628c6c/propcache-0.2.0-cp311-cp311-win32.whl", hash = "sha256:5f2564ec89058ee7c7989a7b719115bdfe2a2fb8e7a4543b8d1c0cc4cf6478c1", size = 40473 },
    { url = "https://files.pythonhosted.org/packages/83/c5/e89fc428ccdc897ade08cd7605f174c69390147526627a7650fb883e0cd0/propcache-0.2.0-cp311-cp311-win_amd64.whl", hash = "sha256:6e2e54267980349b723cff366d1e29b138b9a60fa376664a157a342689553f71", size = 44921 },
    { url = "https://files.pythonhosted.org/packages/7c/46/a41ca1097769fc548fc9216ec4c1471b772cc39720eb47ed7e38ef0006a9/propcache-0.2.0-cp312-cp312-macosx_10_13_universal2.whl", hash = "sha256:2ee7606193fb267be4b2e3b32714f2d58cad27217638db98a60f9efb5efeccc2", size = 80800 },
    { url = "https://files.pythonhosted.org/packages/75/4f/93df46aab9cc473498ff56be39b5f6ee1e33529223d7a4d8c0a6101a9ba2/propcache-0.2.0-cp312-cp312-macosx_10_13_x86_64.whl", hash = "sha256:91ee8fc02ca52e24bcb77b234f22afc03288e1dafbb1f88fe24db308910c4ac7", size = 46443 },
    { url = "https://files.pythonhosted.org/packages/0b/17/308acc6aee65d0f9a8375e36c4807ac6605d1f38074b1581bd4042b9fb37/propcache-0.2.0-cp312-cp312-macosx_11_0_arm64.whl", hash = "sha256:2e900bad2a8456d00a113cad8c13343f3b1f327534e3589acc2219729237a2e8", size = 45676 },
    { url = "https://files.pythonhosted.org/packages/65/44/626599d2854d6c1d4530b9a05e7ff2ee22b790358334b475ed7c89f7d625/propcache-0.2.0-cp312-cp312-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:f52a68c21363c45297aca15561812d542f8fc683c85201df0bebe209e349f793", size = 246191 },
    { url = "https://files.pythonhosted.org/packages/f2/df/5d996d7cb18df076debae7d76ac3da085c0575a9f2be6b1f707fe227b54c/propcache-0.2.0-cp312-cp312-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:1e41d67757ff4fbc8ef2af99b338bfb955010444b92929e9e55a6d4dcc3c4f09", size = 251791 },
    { url = "https://files.pythonhosted.org/packages/2e/6d/9f91e5dde8b1f662f6dd4dff36098ed22a1ef4e08e1316f05f4758f1576c/propcache-0.2.0-cp312-cp312-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:a64e32f8bd94c105cc27f42d3b658902b5bcc947ece3c8fe7bc1b05982f60e89", size = 253434 },
    { url = "https://files.pythonhosted.org/packages/3c/e9/1b54b7e26f50b3e0497cd13d3483d781d284452c2c50dd2a615a92a087a3/propcache-0.2.0-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:55346705687dbd7ef0d77883ab4f6fabc48232f587925bdaf95219bae072491e", size = 248150 },
    { url = "https://files.pythonhosted.org/packages/a7/ef/a35bf191c8038fe3ce9a414b907371c81d102384eda5dbafe6f4dce0cf9b/propcache-0.2.0-cp312-cp312-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:00181262b17e517df2cd85656fcd6b4e70946fe62cd625b9d74ac9977b64d8d9", size = 233568 },
    { url = "https://files.pythonhosted.org/packages/97/d9/d00bb9277a9165a5e6d60f2142cd1a38a750045c9c12e47ae087f686d781/propcache-0.2.0-cp312-cp312-musllinux_1_2_aarch64.whl", hash = "sha256:6994984550eaf25dd7fc7bd1b700ff45c894149341725bb4edc67f0ffa94efa4", size = 229874 },
    { url = "https://files.pythonhosted.org/packages/8e/78/c123cf22469bdc4b18efb78893e69c70a8b16de88e6160b69ca6bdd88b5d/propcache-0.2.0-cp312-cp312-musllinux_1_2_armv7l.whl", hash = "sha256:56295eb1e5f3aecd516d91b00cfd8bf3a13991de5a479df9e27dd569ea23959c", size = 225857 },
    { url = "https://files.pythonhosted.org/packages/31/1b/fd6b2f1f36d028820d35475be78859d8c89c8f091ad30e377ac49fd66359/propcache-0.2.0-cp312-cp312-musllinux_1_2_i686.whl", hash = "sha256:439e76255daa0f8151d3cb325f6dd4a3e93043e6403e6491813bcaaaa8733887", size = 227604 },
    { url = "https://files.pythonhosted.org/packages/99/36/b07be976edf77a07233ba712e53262937625af02154353171716894a86a6/propcache-0.2.0-cp312-cp312-musllinux_1_2_ppc64le.whl", hash = "sha256:f6475a1b2ecb310c98c28d271a30df74f9dd436ee46d09236a6b750a7599ce57", size = 238430 },
    { url = "https://files.pythonhosted.org/packages/0d/64/5822f496c9010e3966e934a011ac08cac8734561842bc7c1f65586e0683c/propcache-0.2.0-cp312-cp312-musllinux_1_2_s390x.whl", hash = "sha256:3444cdba6628accf384e349014084b1cacd866fbb88433cd9d279d90a54e0b23", size = 244814 },
    { url = "https://files.pythonhosted.org/packages/fd/bd/8657918a35d50b18a9e4d78a5df7b6c82a637a311ab20851eef4326305c1/propcache-0.2.0-cp312-cp312-musllinux_1_2_x86_64.whl", hash = "sha256:4a9d9b4d0a9b38d1c391bb4ad24aa65f306c6f01b512e10a8a34a2dc5675d348", size = 235922 },
    { url = "https://files.pythonhosted.org/packages/a8/6f/ec0095e1647b4727db945213a9f395b1103c442ef65e54c62e92a72a3f75/propcache-0.2.0-cp312-cp312-win32.whl", hash = "sha256:69d3a98eebae99a420d4b28756c8ce6ea5a29291baf2dc9ff9414b42676f61d5", size = 40177 },
    { url = "https://files.pythonhosted.org/packages/20/a2/bd0896fdc4f4c1db46d9bc361c8c79a9bf08ccc08ba054a98e38e7ba1557/propcache-0.2.0-cp312-cp312-win_amd64.whl", hash = "sha256:ad9c9b99b05f163109466638bd30ada1722abb01bbb85c739c50b6dc11f92dc3", size = 44446 },
    { url = "https://files.pythonhosted.org/packages/3d/b6/e6d98278f2d49b22b4d033c9f792eda783b9ab2094b041f013fc69bcde87/propcache-0.2.0-py3-none-any.whl", hash = "sha256:2ccc28197af5313706511fab3a8b66dcd6da067a1331372c82ea1cb74285e036", size = 11603 },
]

[[package]]
name = "ptyprocess"
version = "0.7.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/20/e5/16ff212c1e452235a90aeb09066144d0c5a6a8c0834397e03f5224495c4e/ptyprocess-0.7.0.tar.gz", hash = "sha256:5c5d0a3b48ceee0b48485e0c26037c0acd7d29765ca3fbb5cb3831d347423220", size = 70762 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/22/a6/858897256d0deac81a172289110f31629fc4cee19b6f01283303e18c8db3/ptyprocess-0.7.0-py2.py3-none-any.whl", hash = "sha256:4b41f3967fce3af57cc7e94b888626c18bf37a083e3651ca8feeb66d492fef35", size = 13993 },
]

[[package]]
name = "pyaes"
version = "1.6.1"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/44/66/2c17bae31c906613795711fc78045c285048168919ace2220daa372c7d72/pyaes-1.6.1.tar.gz", hash = "sha256:02c1b1405c38d3c370b085fb952dd8bea3fadcee6411ad99f312cc129c536d8f", size = 28536 }

[[package]]
name = "pyasn1"
version = "0.6.1"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/ba/e9/01f1a64245b89f039897cb0130016d79f77d52669aae6ee7b159a6c4c018/pyasn1-0.6.1.tar.gz", hash = "sha256:6f580d2bdd84365380830acf45550f2511469f673cb4a5ae3857a3170128b034", size = 145322 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/c8/f1/d6a797abb14f6283c0ddff96bbdd46937f64122b8c925cab503dd37f8214/pyasn1-0.6.1-py3-none-any.whl", hash = "sha256:0d632f46f2ba09143da3a8afe9e33fb6f92fa2320ab7e886e2d0f7672af84629", size = 83135 },
]

[[package]]
name = "pycountry"
version = "24.6.1"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/76/57/c389fa68c50590881a75b7883eeb3dc15e9e73a0fdc001cdd45c13290c92/pycountry-24.6.1.tar.gz", hash = "sha256:b61b3faccea67f87d10c1f2b0fc0be714409e8fcdcc1315613174f6466c10221", size = 6043910 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/b1/ec/1fb891d8a2660716aadb2143235481d15ed1cbfe3ad669194690b0604492/pycountry-24.6.1-py3-none-any.whl", hash = "sha256:f1a4fb391cd7214f8eefd39556d740adcc233c778a27f8942c8dca351d6ce06f", size = 6335189 },
]

[[package]]
name = "pycparser"
version = "2.22"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/1d/b2/31537cf4b1ca988837256c910a668b553fceb8f069bedc4b1c826024b52c/pycparser-2.22.tar.gz", hash = "sha256:491c8be9c040f5390f5bf44a5b07752bd07f56edf992381b05c701439eec10f6", size = 172736 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/13/a3/a812df4e2dd5696d1f351d58b8fe16a405b234ad2886a0dab9183fb78109/pycparser-2.22-py3-none-any.whl", hash = "sha256:c3702b6d3dd8c7abc1afa565d7e63d53a1d0bd86cdc24edd75470f4de499cfcc", size = 117552 },
]

[[package]]
name = "pydub"
version = "0.25.1"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/fe/9a/e6bca0eed82db26562c73b5076539a4a08d3cffd19c3cc5913a3e61145fd/pydub-0.25.1.tar.gz", hash = "sha256:980a33ce9949cab2a569606b65674d748ecbca4f0796887fd6f46173a7b0d30f", size = 38326 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/a6/53/d78dc063216e62fc55f6b2eebb447f6a4b0a59f55c8406376f76bf959b08/pydub-0.25.1-py2.py3-none-any.whl", hash = "sha256:65617e33033874b59d87db603aa1ed450633288aefead953b30bded59cb599a6", size = 32327 },
]

[[package]]
name = "pygments"
version = "2.18.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/8e/62/8336eff65bcbc8e4cb5d05b55faf041285951b6e80f33e2bff2024788f31/pygments-2.18.0.tar.gz", hash = "sha256:786ff802f32e91311bff3889f6e9a86e81505fe99f2735bb6d60ae0c5004f199", size = 4891905 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/f7/3f/01c8b82017c199075f8f788d0d906b9ffbbc5a47dc9918a945e13d5a2bda/pygments-2.18.0-py3-none-any.whl", hash = "sha256:b8e6aca0523f3ab76fee51799c488e38782ac06eafcf95e7ba832985c8e7b13a", size = 1205513 },
]

[[package]]
name = "pynacl"
version = "1.5.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "cffi" },
]
sdist = { url = "https://files.pythonhosted.org/packages/a7/22/27582568be639dfe22ddb3902225f91f2f17ceff88ce80e4db396c8986da/PyNaCl-1.5.0.tar.gz", hash = "sha256:8ac7448f09ab85811607bdd21ec2464495ac8b7c66d146bf545b0f08fb9220ba", size = 3392854 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/ce/75/0b8ede18506041c0bf23ac4d8e2971b4161cd6ce630b177d0a08eb0d8857/PyNaCl-1.5.0-cp36-abi3-macosx_10_10_universal2.whl", hash = "sha256:401002a4aaa07c9414132aaed7f6836ff98f59277a234704ff66878c2ee4a0d1", size = 349920 },
    { url = "https://files.pythonhosted.org/packages/59/bb/fddf10acd09637327a97ef89d2a9d621328850a72f1fdc8c08bdf72e385f/PyNaCl-1.5.0-cp36-abi3-manylinux_2_17_aarch64.manylinux2014_aarch64.manylinux_2_24_aarch64.whl", hash = "sha256:52cb72a79269189d4e0dc537556f4740f7f0a9ec41c1322598799b0bdad4ef92", size = 601722 },
    { url = "https://files.pythonhosted.org/packages/5d/70/87a065c37cca41a75f2ce113a5a2c2aa7533be648b184ade58971b5f7ccc/PyNaCl-1.5.0-cp36-abi3-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:a36d4a9dda1f19ce6e03c9a784a2921a4b726b02e1c736600ca9c22029474394", size = 680087 },
    { url = "https://files.pythonhosted.org/packages/ee/87/f1bb6a595f14a327e8285b9eb54d41fef76c585a0edef0a45f6fc95de125/PyNaCl-1.5.0-cp36-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.manylinux_2_24_x86_64.whl", hash = "sha256:0c84947a22519e013607c9be43706dd42513f9e6ae5d39d3613ca1e142fba44d", size = 856678 },
    { url = "https://files.pythonhosted.org/packages/66/28/ca86676b69bf9f90e710571b67450508484388bfce09acf8a46f0b8c785f/PyNaCl-1.5.0-cp36-abi3-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:06b8f6fa7f5de8d5d2f7573fe8c863c051225a27b61e6860fd047b1775807858", size = 1133660 },
    { url = "https://files.pythonhosted.org/packages/3d/85/c262db650e86812585e2bc59e497a8f59948a005325a11bbbc9ecd3fe26b/PyNaCl-1.5.0-cp36-abi3-musllinux_1_1_aarch64.whl", hash = "sha256:a422368fc821589c228f4c49438a368831cb5bbc0eab5ebe1d7fac9dded6567b", size = 663824 },
    { url = "https://files.pythonhosted.org/packages/fd/1a/cc308a884bd299b651f1633acb978e8596c71c33ca85e9dc9fa33a5399b9/PyNaCl-1.5.0-cp36-abi3-musllinux_1_1_x86_64.whl", hash = "sha256:61f642bf2378713e2c2e1de73444a3778e5f0a38be6fee0fe532fe30060282ff", size = 1117912 },
    { url = "https://files.pythonhosted.org/packages/25/2d/b7df6ddb0c2a33afdb358f8af6ea3b8c4d1196ca45497dd37a56f0c122be/PyNaCl-1.5.0-cp36-abi3-win32.whl", hash = "sha256:e46dae94e34b085175f8abb3b0aaa7da40767865ac82c928eeb9e57e1ea8a543", size = 204624 },
    { url = "https://files.pythonhosted.org/packages/5e/22/d3db169895faaf3e2eda892f005f433a62db2decbcfbc2f61e6517adfa87/PyNaCl-1.5.0-cp36-abi3-win_amd64.whl", hash = "sha256:20f42270d27e1b6a29f54032090b972d97f0a1b0948cc52392041ef7831fee93", size = 212141 },
]

[[package]]
name = "pyperclip"
version = "1.9.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/30/23/2f0a3efc4d6a32f3b63cdff36cd398d9701d26cda58e3ab97ac79fb5e60d/pyperclip-1.9.0.tar.gz", hash = "sha256:b7de0142ddc81bfc5c7507eea19da920b92252b548b96186caf94a5e2527d310", size = 20961 }

[[package]]
name = "pyreadline"
version = "2.1"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/bc/7c/d724ef1ec3ab2125f38a1d53285745445ec4a8f19b9bb0761b4064316679/pyreadline-2.1.zip", hash = "sha256:4530592fc2e85b25b1a9f79664433da09237c1a270e4d78ea5aa3a2c7229e2d1", size = 109189 }

[[package]]
name = "python-dotenv"
version = "1.0.1"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/bc/57/e84d88dfe0aec03b7a2d4327012c1627ab5f03652216c63d49846d7a6c58/python-dotenv-1.0.1.tar.gz", hash = "sha256:e324ee90a023d808f1959c46bcbc04446a10ced277783dc6ee09987c37ec10ca", size = 39115 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/6a/3e/b68c118422ec867fa7ab88444e1274aa40681c606d59ac27de5a5588f082/python_dotenv-1.0.1-py3-none-any.whl", hash = "sha256:f7b63ef50f1b690dddf550d03497b66d609393b40b564ed0d674909a68ebf16a", size = 19863 },
]

[[package]]
name = "readchar"
version = "4.2.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/18/31/2934981710c63afa9c58947d2e676093ce4bb6c7ce60aac2fcc4be7d98d0/readchar-4.2.0.tar.gz", hash = "sha256:44807cbbe377b72079fea6cba8aa91c809982d7d727b2f0dbb2d1a8084914faa", size = 9691 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/7b/6f/ca076ad4d18b3d33c31c304fb7e68dd9ce2bfdb49fb8874611ad7c55e969/readchar-4.2.0-py3-none-any.whl", hash = "sha256:2a587a27c981e6d25a518730ad4c88c429c315439baa6fda55d7a8b3ac4cb62a", size = 9349 },
]

[[package]]
name = "requests"
version = "2.32.3"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "certifi" },
    { name = "charset-normalizer" },
    { name = "idna" },
    { name = "urllib3" },
]
sdist = { url = "https://files.pythonhosted.org/packages/63/70/2bf7780ad2d390a8d301ad0b550f1581eadbd9a20f896afe06353c2a2913/requests-2.32.3.tar.gz", hash = "sha256:55365417734eb18255590a9ff9eb97e9e1da868d4ccd6402399eaf68af20a760", size = 131218 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/f9/9b/335f9764261e915ed497fcdeb11df5dfd6f7bf257d4a6a2a686d80da4d54/requests-2.32.3-py3-none-any.whl", hash = "sha256:70761cfe03c773ceb22aa2f671b4757976145175cdfca038c02654d061d6dcc6", size = 64928 },
]

[[package]]
name = "rich"
version = "13.9.3"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "markdown-it-py" },
    { name = "pygments" },
]
sdist = { url = "https://files.pythonhosted.org/packages/d9/e9/cf9ef5245d835065e6673781dbd4b8911d352fb770d56cf0879cf11b7ee1/rich-13.9.3.tar.gz", hash = "sha256:bc1e01b899537598cf02579d2b9f4a415104d3fc439313a7a2c165d76557a08e", size = 222889 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/9a/e2/10e9819cf4a20bd8ea2f5dabafc2e6bf4a78d6a0965daeb60a4b34d1c11f/rich-13.9.3-py3-none-any.whl", hash = "sha256:9836f5096eb2172c9e77df411c1b009bace4193d6a481d534fea75ebba758283", size = 242157 },
]

[[package]]
name = "rsa"
version = "4.9"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "pyasn1" },
]
sdist = { url = "https://files.pythonhosted.org/packages/aa/65/7d973b89c4d2351d7fb232c2e452547ddfa243e93131e7cfa766da627b52/rsa-4.9.tar.gz", hash = "sha256:e38464a49c6c85d7f1351b0126661487a7e0a14a50f1675ec50eb34d4f20ef21", size = 29711 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/49/97/fa78e3d2f65c02c8e1268b9aba606569fe97f6c8f7c2d74394553347c145/rsa-4.9-py3-none-any.whl", hash = "sha256:90260d9058e514786967344d0ef75fa8727eed8a7d2e43ce9f4bcf1b536174f7", size = 34315 },
]

[[package]]
name = "ruff"
version = "0.7.1"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/a6/21/5c6e05e0fd3fbb41be4fb92edbc9a04de70baf60adb61435ce0c6b8c3d55/ruff-0.7.1.tar.gz", hash = "sha256:9d8a41d4aa2dad1575adb98a82870cf5db5f76b2938cf2206c22c940034a36f4", size = 3181670 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/65/45/8a20a9920175c9c4892b2420f80ff3cf14949cf3067118e212f9acd9c908/ruff-0.7.1-py3-none-linux_armv6l.whl", hash = "sha256:cb1bc5ed9403daa7da05475d615739cc0212e861b7306f314379d958592aaa89", size = 10389268 },
    { url = "https://files.pythonhosted.org/packages/1b/d3/2f8382db2cf4f9488e938602e33e36287f9d26cb283aa31f11c31297ce79/ruff-0.7.1-py3-none-macosx_10_12_x86_64.whl", hash = "sha256:27c1c52a8d199a257ff1e5582d078eab7145129aa02721815ca8fa4f9612dc35", size = 10188348 },
    { url = "https://files.pythonhosted.org/packages/a2/31/7d14e2a88da351200f844b7be889a0845d9e797162cf76b136d21b832a23/ruff-0.7.1-py3-none-macosx_11_0_arm64.whl", hash = "sha256:588a34e1ef2ea55b4ddfec26bbe76bc866e92523d8c6cdec5e8aceefeff02d99", size = 9841448 },
    { url = "https://files.pythonhosted.org/packages/db/99/738cafdc768eceeca0bd26c6f03e213aa91203d2278e1d95b1c31c4ece41/ruff-0.7.1-py3-none-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:94fc32f9cdf72dc75c451e5f072758b118ab8100727168a3df58502b43a599ca", size = 10674864 },
    { url = "https://files.pythonhosted.org/packages/fe/12/bcf2836b50eab53c65008383e7d55201e490d75167c474f14a16e1af47d2/ruff-0.7.1-py3-none-manylinux_2_17_armv7l.manylinux2014_armv7l.whl", hash = "sha256:985818742b833bffa543a84d1cc11b5e6871de1b4e0ac3060a59a2bae3969250", size = 10192105 },
    { url = "https://files.pythonhosted.org/packages/2b/71/261d5d668bf98b6c44e89bfb5dfa4cb8cb6c8b490a201a3d8030e136ea4f/ruff-0.7.1-py3-none-manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:32f1e8a192e261366c702c5fb2ece9f68d26625f198a25c408861c16dc2dea9c", size = 11194144 },
    { url = "https://files.pythonhosted.org/packages/90/1f/0926d18a3b566fa6e7b3b36093088e4ffef6b6ba4ea85a462d9a93f7e35c/ruff-0.7.1-py3-none-manylinux_2_17_ppc64.manylinux2014_ppc64.whl", hash = "sha256:699085bf05819588551b11751eff33e9ca58b1b86a6843e1b082a7de40da1565", size = 11917066 },
    { url = "https://files.pythonhosted.org/packages/cd/a8/9fac41f128b6a44ab4409c1493430b4ee4b11521e8aeeca19bfe1ce851f9/ruff-0.7.1-py3-none-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:344cc2b0814047dc8c3a8ff2cd1f3d808bb23c6658db830d25147339d9bf9ea7", size = 11458821 },
    { url = "https://files.pythonhosted.org/packages/25/cd/59644168f086ab13fe4e02943b9489a0aa710171f66b178e179df5383554/ruff-0.7.1-py3-none-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:4316bbf69d5a859cc937890c7ac7a6551252b6a01b1d2c97e8fc96e45a7c8b4a", size = 12700379 },
    { url = "https://files.pythonhosted.org/packages/fb/30/3bac63619eb97174661829c07fc46b2055a053dee72da29d7c304c1cd2c0/ruff-0.7.1-py3-none-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:79d3af9dca4c56043e738a4d6dd1e9444b6d6c10598ac52d146e331eb155a8ad", size = 11019813 },
    { url = "https://files.pythonhosted.org/packages/4b/af/f567b885b5cb3bcdbcca3458ebf210cc8c9c7a9f61c332d3c2a050c3b21e/ruff-0.7.1-py3-none-musllinux_1_2_aarch64.whl", hash = "sha256:c5c121b46abde94a505175524e51891f829414e093cd8326d6e741ecfc0a9112", size = 10662146 },
    { url = "https://files.pythonhosted.org/packages/bc/ad/eb930d3ad117a9f2f7261969c21559ebd82bb13b6e8001c7caed0d44be5f/ruff-0.7.1-py3-none-musllinux_1_2_armv7l.whl", hash = "sha256:8422104078324ea250886954e48f1373a8fe7de59283d747c3a7eca050b4e378", size = 10256911 },
    { url = "https://files.pythonhosted.org/packages/20/d5/af292ce70a016fcec792105ca67f768b403dd480a11888bc1f418fed0dd5/ruff-0.7.1-py3-none-musllinux_1_2_i686.whl", hash = "sha256:56aad830af8a9db644e80098fe4984a948e2b6fc2e73891538f43bbe478461b8", size = 10767488 },
    { url = "https://files.pythonhosted.org/packages/24/85/cc04a3bd027f433bebd2a097e63b3167653c079f7f13d8f9a1178e693412/ruff-0.7.1-py3-none-musllinux_1_2_x86_64.whl", hash = "sha256:658304f02f68d3a83c998ad8bf91f9b4f53e93e5412b8f2388359d55869727fd", size = 11093368 },
    { url = "https://files.pythonhosted.org/packages/0b/fb/c39cbf32d1f3e318674b8622f989417231794926b573f76dd4d0ca49f0f1/ruff-0.7.1-py3-none-win32.whl", hash = "sha256:b517a2011333eb7ce2d402652ecaa0ac1a30c114fbbd55c6b8ee466a7f600ee9", size = 8594180 },
    { url = "https://files.pythonhosted.org/packages/5a/71/ec8cdea34ecb90c830ca60d54ac7b509a7b5eab50fae27e001d4470fe813/ruff-0.7.1-py3-none-win_amd64.whl", hash = "sha256:f38c41fcde1728736b4eb2b18850f6d1e3eedd9678c914dede554a70d5241307", size = 9419751 },
    { url = "https://files.pythonhosted.org/packages/79/7b/884553415e9f0a9bf358ed52fb68b934e67ef6c5a62397ace924a1afdf9a/ruff-0.7.1-py3-none-win_arm64.whl", hash = "sha256:19aa200ec824c0f36d0c9114c8ec0087082021732979a359d6f3c390a6ff2a37", size = 8717402 },
]

[[package]]
name = "runs"
version = "1.2.2"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "xmod" },
]
sdist = { url = "https://files.pythonhosted.org/packages/26/6d/b9aace390f62db5d7d2c77eafce3d42774f27f1829d24fa9b6f598b3ef71/runs-1.2.2.tar.gz", hash = "sha256:9dc1815e2895cfb3a48317b173b9f1eac9ba5549b36a847b5cc60c3bf82ecef1", size = 5474 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/86/d6/17caf2e4af1dec288477a0cbbe4a96fbc9b8a28457dce3f1f452630ce216/runs-1.2.2-py3-none-any.whl", hash = "sha256:0980dcbc25aba1505f307ac4f0e9e92cbd0be2a15a1e983ee86c24c87b839dfd", size = 7033 },
]

[[package]]
name = "scipy"
version = "1.14.1"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "numpy" },
]
sdist = { url = "https://files.pythonhosted.org/packages/62/11/4d44a1f274e002784e4dbdb81e0ea96d2de2d1045b2132d5af62cc31fd28/scipy-1.14.1.tar.gz", hash = "sha256:5a275584e726026a5699459aa72f828a610821006228e841b94275c4a7c08417", size = 58620554 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/b2/ab/070ccfabe870d9f105b04aee1e2860520460ef7ca0213172abfe871463b9/scipy-1.14.1-cp311-cp311-macosx_10_13_x86_64.whl", hash = "sha256:2da0469a4ef0ecd3693761acbdc20f2fdeafb69e6819cc081308cc978153c675", size = 39076999 },
    { url = "https://files.pythonhosted.org/packages/a7/c5/02ac82f9bb8f70818099df7e86c3ad28dae64e1347b421d8e3adf26acab6/scipy-1.14.1-cp311-cp311-macosx_12_0_arm64.whl", hash = "sha256:c0ee987efa6737242745f347835da2cc5bb9f1b42996a4d97d5c7ff7928cb6f2", size = 29894570 },
    { url = "https://files.pythonhosted.org/packages/ed/05/7f03e680cc5249c4f96c9e4e845acde08eb1aee5bc216eff8a089baa4ddb/scipy-1.14.1-cp311-cp311-macosx_14_0_arm64.whl", hash = "sha256:3a1b111fac6baec1c1d92f27e76511c9e7218f1695d61b59e05e0fe04dc59617", size = 23103567 },
    { url = "https://files.pythonhosted.org/packages/5e/fc/9f1413bef53171f379d786aabc104d4abeea48ee84c553a3e3d8c9f96a9c/scipy-1.14.1-cp311-cp311-macosx_14_0_x86_64.whl", hash = "sha256:8475230e55549ab3f207bff11ebfc91c805dc3463ef62eda3ccf593254524ce8", size = 25499102 },
    { url = "https://files.pythonhosted.org/packages/c2/4b/b44bee3c2ddc316b0159b3d87a3d467ef8d7edfd525e6f7364a62cd87d90/scipy-1.14.1-cp311-cp311-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:278266012eb69f4a720827bdd2dc54b2271c97d84255b2faaa8f161a158c3b37", size = 35586346 },
    { url = "https://files.pythonhosted.org/packages/93/6b/701776d4bd6bdd9b629c387b5140f006185bd8ddea16788a44434376b98f/scipy-1.14.1-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:fef8c87f8abfb884dac04e97824b61299880c43f4ce675dd2cbeadd3c9b466d2", size = 41165244 },
    { url = "https://files.pythonhosted.org/packages/06/57/e6aa6f55729a8f245d8a6984f2855696c5992113a5dc789065020f8be753/scipy-1.14.1-cp311-cp311-musllinux_1_2_x86_64.whl", hash = "sha256:b05d43735bb2f07d689f56f7b474788a13ed8adc484a85aa65c0fd931cf9ccd2", size = 42817917 },
    { url = "https://files.pythonhosted.org/packages/ea/c2/5ecadc5fcccefaece775feadcd795060adf5c3b29a883bff0e678cfe89af/scipy-1.14.1-cp311-cp311-win_amd64.whl", hash = "sha256:716e389b694c4bb564b4fc0c51bc84d381735e0d39d3f26ec1af2556ec6aad94", size = 44781033 },
    { url = "https://files.pythonhosted.org/packages/c0/04/2bdacc8ac6387b15db6faa40295f8bd25eccf33f1f13e68a72dc3c60a99e/scipy-1.14.1-cp312-cp312-macosx_10_13_x86_64.whl", hash = "sha256:631f07b3734d34aced009aaf6fedfd0eb3498a97e581c3b1e5f14a04164a456d", size = 39128781 },
    { url = "https://files.pythonhosted.org/packages/c8/53/35b4d41f5fd42f5781dbd0dd6c05d35ba8aa75c84ecddc7d44756cd8da2e/scipy-1.14.1-cp312-cp312-macosx_12_0_arm64.whl", hash = "sha256:af29a935803cc707ab2ed7791c44288a682f9c8107bc00f0eccc4f92c08d6e07", size = 29939542 },
    { url = "https://files.pythonhosted.org/packages/66/67/6ef192e0e4d77b20cc33a01e743b00bc9e68fb83b88e06e636d2619a8767/scipy-1.14.1-cp312-cp312-macosx_14_0_arm64.whl", hash = "sha256:2843f2d527d9eebec9a43e6b406fb7266f3af25a751aa91d62ff416f54170bc5", size = 23148375 },
    { url = "https://files.pythonhosted.org/packages/f6/32/3a6dedd51d68eb7b8e7dc7947d5d841bcb699f1bf4463639554986f4d782/scipy-1.14.1-cp312-cp312-macosx_14_0_x86_64.whl", hash = "sha256:eb58ca0abd96911932f688528977858681a59d61a7ce908ffd355957f7025cfc", size = 25578573 },
    { url = "https://files.pythonhosted.org/packages/f0/5a/efa92a58dc3a2898705f1dc9dbaf390ca7d4fba26d6ab8cfffb0c72f656f/scipy-1.14.1-cp312-cp312-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:30ac8812c1d2aab7131a79ba62933a2a76f582d5dbbc695192453dae67ad6310", size = 35319299 },
    { url = "https://files.pythonhosted.org/packages/8e/ee/8a26858ca517e9c64f84b4c7734b89bda8e63bec85c3d2f432d225bb1886/scipy-1.14.1-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:8f9ea80f2e65bdaa0b7627fb00cbeb2daf163caa015e59b7516395fe3bd1e066", size = 40849331 },
    { url = "https://files.pythonhosted.org/packages/a5/cd/06f72bc9187840f1c99e1a8750aad4216fc7dfdd7df46e6280add14b4822/scipy-1.14.1-cp312-cp312-musllinux_1_2_x86_64.whl", hash = "sha256:edaf02b82cd7639db00dbff629995ef185c8df4c3ffa71a5562a595765a06ce1", size = 42544049 },
    { url = "https://files.pythonhosted.org/packages/aa/7d/43ab67228ef98c6b5dd42ab386eae2d7877036970a0d7e3dd3eb47a0d530/scipy-1.14.1-cp312-cp312-win_amd64.whl", hash = "sha256:2ff38e22128e6c03ff73b6bb0f85f897d2362f8c052e3b8ad00532198fbdae3f", size = 44521212 },
]

[[package]]
name = "scp"
version = "0.15.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "paramiko" },
]
sdist = { url = "https://files.pythonhosted.org/packages/d6/1c/d213e1c6651d0bd37636b21b1ba9b895f276e8057f882c9f944931e4f002/scp-0.15.0.tar.gz", hash = "sha256:f1b22e9932123ccf17eebf19e0953c6e9148f589f93d91b872941a696305c83f", size = 13905 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/79/b3/561cd6afa959e9dd522af12acc4f803e8bab1bd0e383bffc5211721c5fcb/scp-0.15.0-py2.py3-none-any.whl", hash = "sha256:9e7f721e5ac563c33eb0831d0f949c6342f1c28c3bdc3b02f39d77b5ea20df7e", size = 8753 },
]

[[package]]
name = "send2trash"
version = "1.8.3"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/fd/3a/aec9b02217bb79b87bbc1a21bc6abc51e3d5dcf65c30487ac96c0908c722/Send2Trash-1.8.3.tar.gz", hash = "sha256:b18e7a3966d99871aefeb00cfbcfdced55ce4871194810fc71f4aa484b953abf", size = 17394 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/40/b0/4562db6223154aa4e22f939003cb92514c79f3d4dccca3444253fd17f902/Send2Trash-1.8.3-py3-none-any.whl", hash = "sha256:0c31227e0bd08961c7665474a3d1ef7193929fedda4233843689baa056be46c9", size = 18072 },
]

[[package]]
name = "setuptools"
version = "75.2.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/07/37/b31be7e4b9f13b59cde9dcaeff112d401d49e0dc5b37ed4a9fc8fb12f409/setuptools-75.2.0.tar.gz", hash = "sha256:753bb6ebf1f465a1912e19ed1d41f403a79173a9acf66a42e7e6aec45c3c16ec", size = 1350308 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/31/2d/90165d51ecd38f9a02c6832198c13a4e48652485e2ccf863ebb942c531b6/setuptools-75.2.0-py3-none-any.whl", hash = "sha256:a7fcb66f68b4d9e8e66b42f9876150a3371558f98fa32222ffaa5bced76406f8", size = 1249825 },
]

[[package]]
name = "six"
version = "1.16.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/71/39/171f1c67cd00715f190ba0b100d606d440a28c93c7714febeca8b79af85e/six-1.16.0.tar.gz", hash = "sha256:1e61c37477a1626458e36f7b1d82aa5c9b094fa4802892072e49de9c60c4c926", size = 34041 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/d9/5a/e7c31adbe875f2abbb91bd84cf2dc52d792b5a01506781dbcf25c91daf11/six-1.16.0-py2.py3-none-any.whl", hash = "sha256:8abb2f1d86890a2dfb989f9a77cfcfd3e47c2a354b01111771326f8aa26e0254", size = 11053 },
]

[[package]]
name = "soundfile"
version = "0.12.1"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "cffi" },
]
sdist = { url = "https://files.pythonhosted.org/packages/6f/96/5ff33900998bad58d5381fd1acfcdac11cbea4f08fc72ac1dc25ffb13f6a/soundfile-0.12.1.tar.gz", hash = "sha256:e8e1017b2cf1dda767aef19d2fd9ee5ebe07e050d430f77a0a7c66ba08b8cdae", size = 43184 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/04/bc/cd845c2dbb4d257c744cd58a5bcdd9f6d235ca317e7e22e49564ec88dcd9/soundfile-0.12.1-py2.py3-none-any.whl", hash = "sha256:828a79c2e75abab5359f780c81dccd4953c45a2c4cd4f05ba3e233ddf984b882", size = 24030 },
    { url = "https://files.pythonhosted.org/packages/c8/73/059c84343be6509b480013bf1eeb11b96c5f9eb48deff8f83638011f6b2c/soundfile-0.12.1-py2.py3-none-macosx_10_9_x86_64.whl", hash = "sha256:d922be1563ce17a69582a352a86f28ed8c9f6a8bc951df63476ffc310c064bfa", size = 1213305 },
    { url = "https://files.pythonhosted.org/packages/71/87/31d2b9ed58975cec081858c01afaa3c43718eb0f62b5698a876d94739ad0/soundfile-0.12.1-py2.py3-none-macosx_11_0_arm64.whl", hash = "sha256:bceaab5c4febb11ea0554566784bcf4bc2e3977b53946dda2b12804b4fe524a8", size = 1075977 },
    { url = "https://files.pythonhosted.org/packages/ad/bd/0602167a213d9184fc688b1086dc6d374b7ae8c33eccf169f9b50ce6568c/soundfile-0.12.1-py2.py3-none-manylinux_2_17_x86_64.whl", hash = "sha256:2dc3685bed7187c072a46ab4ffddd38cef7de9ae5eb05c03df2ad569cf4dacbc", size = 1257765 },
    { url = "https://files.pythonhosted.org/packages/c1/07/7591f4efd29e65071c3a61b53725036ea8f73366a4920a481ebddaf8d0ca/soundfile-0.12.1-py2.py3-none-manylinux_2_31_x86_64.whl", hash = "sha256:074247b771a181859d2bc1f98b5ebf6d5153d2c397b86ee9e29ba602a8dfe2a6", size = 1174746 },
    { url = "https://files.pythonhosted.org/packages/03/0f/49941ed8a2d94e5b36ea94346fb1d2b22e847fede902e05be4c96f26be7d/soundfile-0.12.1-py2.py3-none-win32.whl", hash = "sha256:59dfd88c79b48f441bbf6994142a19ab1de3b9bb7c12863402c2bc621e49091a", size = 888234 },
    { url = "https://files.pythonhosted.org/packages/50/ff/26a4ee48d0b66625a4e4028a055b9f25bc9d7c7b2d17d21a45137621a50d/soundfile-0.12.1-py2.py3-none-win_amd64.whl", hash = "sha256:0d86924c00b62552b650ddd28af426e3ff2d4dc2e9047dae5b3d8452e0a49a77", size = 1009109 },
]

[[package]]
name = "spinners"
version = "0.0.24"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/d3/91/bb331f0a43e04d950a710f402a0986a54147a35818df0e1658551c8d12e1/spinners-0.0.24.tar.gz", hash = "sha256:1eb6aeb4781d72ab42ed8a01dcf20f3002bf50740d7154d12fb8c9769bf9e27f", size = 5308 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/9f/8e/3310207a68118000ca27ac878b8386123628b335ecb3d4bec4743357f0d1/spinners-0.0.24-py3-none-any.whl", hash = "sha256:2fa30d0b72c9650ad12bbe031c9943b8d441e41b4f5602b0ec977a19f3290e98", size = 5499 },
]

[[package]]
name = "telethon"
version = "1.37.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "pyaes" },
    { name = "rsa" },
]
sdist = { url = "https://files.pythonhosted.org/packages/4e/3c/a94a30abfa8be573dfff298b94a0402789e902a795a19eadf4294387009d/Telethon-1.37.0.tar.gz", hash = "sha256:e5e43cff1c1b34e2f9c2b395215beb6e9bda706b69def7efff4f55b23c9c4374", size = 620160 }

[[package]]
name = "termcolor"
version = "2.5.0"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/37/72/88311445fd44c455c7d553e61f95412cf89054308a1aa2434ab835075fc5/termcolor-2.5.0.tar.gz", hash = "sha256:998d8d27da6d48442e8e1f016119076b690d962507531df4890fcd2db2ef8a6f", size = 13057 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/7f/be/df630c387a0a054815d60be6a97eb4e8f17385d5d6fe660e1c02750062b4/termcolor-2.5.0-py3-none-any.whl", hash = "sha256:37b17b5fc1e604945c2642c872a3764b5d547a48009871aea3edd3afa180afb8", size = 7755 },
]

[[package]]
name = "tomlkit"
version = "0.13.2"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/b1/09/a439bec5888f00a54b8b9f05fa94d7f901d6735ef4e55dcec9bc37b5d8fa/tomlkit-0.13.2.tar.gz", hash = "sha256:fff5fe59a87295b278abd31bec92c15d9bc4a06885ab12bcea52c71119392e79", size = 192885 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/f9/b6/a447b5e4ec71e13871be01ba81f5dfc9d0af7e473da256ff46bc0e24026f/tomlkit-0.13.2-py3-none-any.whl", hash = "sha256:7a974427f6e119197f670fbbbeae7bef749a6c14e793db934baefc1b5f03efde", size = 37955 },
]

[[package]]
name = "tqdm"
version = "4.66.5"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "colorama", marker = "platform_system == 'Windows'" },
]
sdist = { url = "https://files.pythonhosted.org/packages/58/83/6ba9844a41128c62e810fddddd72473201f3eacde02046066142a2d96cc5/tqdm-4.66.5.tar.gz", hash = "sha256:e1020aef2e5096702d8a025ac7d16b1577279c9d63f8375b63083e9a5f0fcbad", size = 169504 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/48/5d/acf5905c36149bbaec41ccf7f2b68814647347b72075ac0b1fe3022fdc73/tqdm-4.66.5-py3-none-any.whl", hash = "sha256:90279a3770753eafc9194a0364852159802111925aa30eb3f9d85b0e805ac7cd", size = 78351 },
]

[[package]]
name = "types-paramiko"
version = "3.5.0.20240928"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "cryptography" },
]
sdist = { url = "https://files.pythonhosted.org/packages/ae/00/733b05fa97328becc7606301d9ae4c7ec7ec9e92324b8420208e397f3ac7/types-paramiko-3.5.0.20240928.tar.gz", hash = "sha256:79dd9b2ee510b76a3b60d8ac1f3f348c45fcecf01347ca79e14db726bbfc442d", size = 23213 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/8e/e5/afb514829e7184e7518a62c014dc364f7a9d47f9112ff26c63835cbf0de5/types_paramiko-3.5.0.20240928-py3-none-any.whl", hash = "sha256:cda0aff4905fe8efe4b5448331a80e943d42a796bd4beb77a3eed3485bc96a85", size = 34016 },
]

[[package]]
name = "types-pillow"
version = "10.2.0.20240822"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/18/4a/4495264dddaa600d65d68bcedb64dcccf9d9da61adff51f7d2ffd8e4c9ce/types-Pillow-10.2.0.20240822.tar.gz", hash = "sha256:559fb52a2ef991c326e4a0d20accb3bb63a7ba8d40eb493e0ecb0310ba52f0d3", size = 35389 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/66/23/e81a5354859831fcf54d488d33b80ba6133ea84f874a9c0ec40a4881e133/types_Pillow-10.2.0.20240822-py3-none-any.whl", hash = "sha256:d9dab025aba07aeb12fd50a6799d4eac52a9603488eca09d7662543983f16c5d", size = 54354 },
]

[[package]]
name = "types-requests"
version = "2.32.0.20241016"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "urllib3" },
]
sdist = { url = "https://files.pythonhosted.org/packages/fa/3c/4f2a430c01a22abd49a583b6b944173e39e7d01b688190a5618bd59a2e22/types-requests-2.32.0.20241016.tar.gz", hash = "sha256:0d9cad2f27515d0e3e3da7134a1b6f28fb97129d86b867f24d9c726452634d95", size = 18065 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/d7/01/485b3026ff90e5190b5e24f1711522e06c79f4a56c8f4b95848ac072e20f/types_requests-2.32.0.20241016-py3-none-any.whl", hash = "sha256:4195d62d6d3e043a4eaaf08ff8a62184584d2e8684e9d2aa178c7915a7da3747", size = 15836 },
]

[[package]]
name = "types-send2trash"
version = "1.8.2.7"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/d3/fa/3c99413e1eb2bafca67aafe681c3d213422fd9565b3851fc9c3753d6ede9/types-Send2Trash-1.8.2.7.tar.gz", hash = "sha256:f471c0dcb6c0f6682eebdbf4498a2f4fe16b4c9c25e64969450334734ac1649c", size = 2725 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/ca/ff/f34aba2dec864d0d97af5c11c9690f429fdf7388a9663cc817b4a6b1f8f7/types_Send2Trash-1.8.2.7-py3-none-any.whl", hash = "sha256:e4796fa3888ad0272ed73e5e2f983f75f5a171ca0b553a7362d902c553478334", size = 3186 },
]

[[package]]
name = "typing-extensions"
version = "4.12.2"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/df/db/f35a00659bc03fec321ba8bce9420de607a1d37f8342eee1863174c69557/typing_extensions-4.12.2.tar.gz", hash = "sha256:1a7ead55c7e559dd4dee8856e3a88b41225abfe1ce8df57b7c13915fe121ffb8", size = 85321 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/26/9f/ad63fc0248c5379346306f8668cda6e2e2e9c95e01216d2b8ffd9ff037d0/typing_extensions-4.12.2-py3-none-any.whl", hash = "sha256:04e5ca0351e0f3f85c6853954072df659d0d13fac324d0072316b67d7794700d", size = 37438 },
]

[[package]]
name = "urllib3"
version = "2.2.3"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/ed/63/22ba4ebfe7430b76388e7cd448d5478814d3032121827c12a2cc287e2260/urllib3-2.2.3.tar.gz", hash = "sha256:e7d814a81dad81e6caf2ec9fdedb284ecc9c73076b62654547cc64ccdcae26e9", size = 300677 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/ce/d9/5f4c13cecde62396b0d3fe530a50ccea91e7dfc1ccf0e09c228841bb5ba8/urllib3-2.2.3-py3-none-any.whl", hash = "sha256:ca899ca043dcb1bafa3e262d73aa25c465bfb49e0bd9dd5d59f1d0acba2f8fac", size = 126338 },
]

[[package]]
name = "wcwidth"
version = "0.2.13"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/6c/63/53559446a878410fc5a5974feb13d31d78d752eb18aeba59c7fef1af7598/wcwidth-0.2.13.tar.gz", hash = "sha256:72ea0c06399eb286d978fdedb6923a9eb47e1c486ce63e9b4e64fc18303972b5", size = 101301 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/fd/84/fd2ba7aafacbad3c4201d395674fc6348826569da3c0937e75505ead3528/wcwidth-0.2.13-py2.py3-none-any.whl", hash = "sha256:3da69048e4540d84af32131829ff948f1e022c1c6bdb8d6102117aac784f6859", size = 34166 },
]

[[package]]
name = "xmod"
version = "1.8.1"
source = { registry = "https://pypi.org/simple" }
sdist = { url = "https://files.pythonhosted.org/packages/72/b2/e3edc608823348e628a919e1d7129e641997afadd946febdd704aecc5881/xmod-1.8.1.tar.gz", hash = "sha256:38c76486b9d672c546d57d8035df0beb7f4a9b088bc3fb2de5431ae821444377", size = 3988 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/33/6b/0dc75b64a764ea1cb8e4c32d1fb273c147304d4e5483cd58be482dc62e45/xmod-1.8.1-py3-none-any.whl", hash = "sha256:a24e9458a4853489042522bdca9e50ee2eac5ab75c809a91150a8a7f40670d48", size = 4610 },
]

[[package]]
name = "yarl"
version = "1.16.0"
source = { registry = "https://pypi.org/simple" }
dependencies = [
    { name = "idna" },
    { name = "multidict" },
    { name = "propcache" },
]
sdist = { url = "https://files.pythonhosted.org/packages/23/52/e9766cc6c2eab7dd1e9749c52c9879317500b46fb97d4105223f86679f93/yarl-1.16.0.tar.gz", hash = "sha256:b6f687ced5510a9a2474bbae96a4352e5ace5fa34dc44a217b0537fec1db00b4", size = 176548 }
wheels = [
    { url = "https://files.pythonhosted.org/packages/0a/00/b29affe83de95e403f8a2a669b5a33f1e7dfe686264008100052eb0b05fd/yarl-1.16.0-cp311-cp311-macosx_10_9_universal2.whl", hash = "sha256:d8643975a0080f361639787415a038bfc32d29208a4bf6b783ab3075a20b1ef3", size = 140120 },
    { url = "https://files.pythonhosted.org/packages/3f/22/bcc9799950281a5d4f646536854839ccdbb965e900827ef0750680f81faf/yarl-1.16.0-cp311-cp311-macosx_10_9_x86_64.whl", hash = "sha256:676d96bafc8c2d0039cea0cd3fd44cee7aa88b8185551a2bb93354668e8315c2", size = 92956 },
    { url = "https://files.pythonhosted.org/packages/33/0f/1b76d853d9d921d68bd9991648be17d34e7ac51e2e20e7658f8ee7e2e2ad/yarl-1.16.0-cp311-cp311-macosx_11_0_arm64.whl", hash = "sha256:d9525f03269e64310416dbe6c68d3b23e5d34aaa8f47193a1c45ac568cecbc49", size = 90891 },
    { url = "https://files.pythonhosted.org/packages/61/19/3666d990c24aae98c748e2c262adc9b3a71e38834df007ac5317f4bbd789/yarl-1.16.0-cp311-cp311-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:8b37d5ec034e668b22cf0ce1074d6c21fd2a08b90d11b1b73139b750a8b0dd97", size = 338857 },
    { url = "https://files.pythonhosted.org/packages/a0/3d/54acbb3cdfcfea03d6a3535cff1e060a2de23e419a4e3955c9661171b8a8/yarl-1.16.0-cp311-cp311-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:4f32c4cb7386b41936894685f6e093c8dfaf0960124d91fe0ec29fe439e201d0", size = 354005 },
    { url = "https://files.pythonhosted.org/packages/15/98/cd9fe3938422c88775c94578a6c145aca89ff8368ff64e6032213ac12403/yarl-1.16.0-cp311-cp311-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:5b8e265a0545637492a7e12fd7038370d66c9375a61d88c5567d0e044ded9202", size = 351195 },
    { url = "https://files.pythonhosted.org/packages/e2/13/b6eff6ea1667aee948ecd6b1c8fb6473234f8e48f49af97be93251869c51/yarl-1.16.0-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:789a3423f28a5fff46fbd04e339863c169ece97c827b44de16e1a7a42bc915d2", size = 342789 },
    { url = "https://files.pythonhosted.org/packages/fe/05/d98e65ea74a7e44bb033b2cf5bcc16edc1d5212bdc5ca7fbb5e380d89f8e/yarl-1.16.0-cp311-cp311-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:f1d1f45e3e8d37c804dca99ab3cf4ab3ed2e7a62cd82542924b14c0a4f46d243", size = 336478 },
    { url = "https://files.pythonhosted.org/packages/7d/47/43de2e94b75f36d84733a35c807d0e33aaf084e98f32e2cbc685102f4ba4/yarl-1.16.0-cp311-cp311-musllinux_1_2_aarch64.whl", hash = "sha256:621280719c4c5dad4c1391160a9b88925bb8b0ff6a7d5af3224643024871675f", size = 346008 },
    { url = "https://files.pythonhosted.org/packages/e2/de/9c2f900ec5e2f2e20329cfe7dcd9452e326d08cb5ecd098c2d4e9987b65c/yarl-1.16.0-cp311-cp311-musllinux_1_2_armv7l.whl", hash = "sha256:ed097b26f18a1f5ff05f661dc36528c5f6735ba4ce8c9645e83b064665131349", size = 343745 },
    { url = "https://files.pythonhosted.org/packages/56/cd/b014dce22e37b77caa37f998c6c47434fd78d01e7be07119629f369f5ee1/yarl-1.16.0-cp311-cp311-musllinux_1_2_i686.whl", hash = "sha256:2f1fe2b2e3ee418862f5ebc0c0083c97f6f6625781382f828f6d4e9b614eba9b", size = 349705 },
    { url = "https://files.pythonhosted.org/packages/07/17/bb191a26f7189423964e008ccb5146ce5258454ef3979f9d4c6860d282c7/yarl-1.16.0-cp311-cp311-musllinux_1_2_ppc64le.whl", hash = "sha256:87dd10bc0618991c66cee0cc65fa74a45f4ecb13bceec3c62d78ad2e42b27a16", size = 360767 },
    { url = "https://files.pythonhosted.org/packages/19/09/7d777369e151991b708a5b35280ea7444621d65af5f0545bcdce5d840867/yarl-1.16.0-cp311-cp311-musllinux_1_2_s390x.whl", hash = "sha256:4199db024b58a8abb2cfcedac7b1292c3ad421684571aeb622a02f242280e8d6", size = 364755 },
    { url = "https://files.pythonhosted.org/packages/00/32/7558997d1d2e53dab15f6db5db49fc6b412b63ede3cb8314e5dd7cff14fe/yarl-1.16.0-cp311-cp311-musllinux_1_2_x86_64.whl", hash = "sha256:99a9dcd4b71dd5f5f949737ab3f356cfc058c709b4f49833aeffedc2652dac56", size = 357087 },
    { url = "https://files.pythonhosted.org/packages/28/20/c49a95a30c57224e5fb0fc83235295684b041300ce508b71821cb042527d/yarl-1.16.0-cp311-cp311-win32.whl", hash = "sha256:a9394c65ae0ed95679717d391c862dece9afacd8fa311683fc8b4362ce8a410c", size = 83030 },
    { url = "https://files.pythonhosted.org/packages/75/e3/2a746721d6f32886d9bafccdb80174349f180ccae0a287f25ba4312a2618/yarl-1.16.0-cp311-cp311-win_amd64.whl", hash = "sha256:5b9101f528ae0f8f65ac9d64dda2bb0627de8a50344b2f582779f32fda747c1d", size = 89616 },
    { url = "https://files.pythonhosted.org/packages/3a/be/82f696c8ce0395c37f62b955202368086e5cc114d5bb9cb1b634cff5e01d/yarl-1.16.0-cp312-cp312-macosx_10_13_universal2.whl", hash = "sha256:4ffb7c129707dd76ced0a4a4128ff452cecf0b0e929f2668ea05a371d9e5c104", size = 141230 },
    { url = "https://files.pythonhosted.org/packages/38/60/45caaa748b53c4b0964f899879fcddc41faa4e0d12c6f0ae3311e8c151ff/yarl-1.16.0-cp312-cp312-macosx_10_13_x86_64.whl", hash = "sha256:1a5e9d8ce1185723419c487758d81ac2bde693711947032cce600ca7c9cda7d6", size = 93515 },
    { url = "https://files.pythonhosted.org/packages/54/bd/33aaca2f824dc1d630729e16e313797e8b24c8f7b6803307e5394274e443/yarl-1.16.0-cp312-cp312-macosx_11_0_arm64.whl", hash = "sha256:d743e3118b2640cef7768ea955378c3536482d95550222f908f392167fe62059", size = 91441 },
    { url = "https://files.pythonhosted.org/packages/af/fa/1ce8ca85489925aabdb8d2e7bbeaf74e7d3e6ac069779d6d6b9c7c62a8ed/yarl-1.16.0-cp312-cp312-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:26768342f256e6e3c37533bf9433f5f15f3e59e3c14b2409098291b3efaceacb", size = 330871 },
    { url = "https://files.pythonhosted.org/packages/f1/2a/a8110a225e498b87315827f8b61d24de35f86041834cf8c9c5544380c46b/yarl-1.16.0-cp312-cp312-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:d1b0796168b953bca6600c5f97f5ed407479889a36ad7d17183366260f29a6b9", size = 340641 },
    { url = "https://files.pythonhosted.org/packages/d0/64/20cd1cb1f60b3ff49e7d75c1a2083352e7c5939368aafa960712c9e53797/yarl-1.16.0-cp312-cp312-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:858728086914f3a407aa7979cab743bbda1fe2bdf39ffcd991469a370dd7414d", size = 340245 },
    { url = "https://files.pythonhosted.org/packages/77/a8/7f38bbefb22eb925a68ad1d8193b05f51515614a6c0ebcadf26e9ae5e5ad/yarl-1.16.0-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:5570e6d47bcb03215baf4c9ad7bf7c013e56285d9d35013541f9ac2b372593e7", size = 336054 },
    { url = "https://files.pythonhosted.org/packages/b4/a6/ac633ea3ea0c4eb1057e6800db1d077e77493b4b3449a4a97b2fbefadef4/yarl-1.16.0-cp312-cp312-manylinux_2_5_i686.manylinux1_i686.manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:66ea8311422a7ba1fc79b4c42c2baa10566469fe5a78500d4e7754d6e6db8724", size = 324405 },
    { url = "https://files.pythonhosted.org/packages/93/cd/4fc87ce9b0df7afb610ffb904f4aef25f59e0ad40a49da19a475facf98b7/yarl-1.16.0-cp312-cp312-musllinux_1_2_aarch64.whl", hash = "sha256:649bddcedee692ee8a9b7b6e38582cb4062dc4253de9711568e5620d8707c2a3", size = 342235 },
    { url = "https://files.pythonhosted.org/packages/9f/bc/38bae4b716da1206849d88e167d3d2c5695ae9b418a3915220947593e5ca/yarl-1.16.0-cp312-cp312-musllinux_1_2_armv7l.whl", hash = "sha256:3a91654adb7643cb21b46f04244c5a315a440dcad63213033826549fa2435f71", size = 340835 },
    { url = "https://files.pythonhosted.org/packages/dc/0f/b9efbc0075916a450cbad41299dff3bdd3393cb1d8378bb831c4a6a836e1/yarl-1.16.0-cp312-cp312-musllinux_1_2_i686.whl", hash = "sha256:b439cae82034ade094526a8f692b9a2b5ee936452de5e4c5f0f6c48df23f8604", size = 344323 },
    { url = "https://files.pythonhosted.org/packages/87/6d/dc483ea1574005f14ef4c5f5f726cf60327b07ac83bd417d98db23e5285f/yarl-1.16.0-cp312-cp312-musllinux_1_2_ppc64le.whl", hash = "sha256:571f781ae8ac463ce30bacebfaef2c6581543776d5970b2372fbe31d7bf31a07", size = 355112 },
    { url = "https://files.pythonhosted.org/packages/10/22/3b7c3728d26b3cc295c51160ae4e2612ab7d3f9df30beece44bf72861730/yarl-1.16.0-cp312-cp312-musllinux_1_2_s390x.whl", hash = "sha256:aa7943f04f36d6cafc0cf53ea89824ac2c37acbdb4b316a654176ab8ffd0f968", size = 361506 },
    { url = "https://files.pythonhosted.org/packages/ad/8d/b7b5d43cf22a020b564ddf7502d83df150d797e34f18f6bf5fe0f12cbd91/yarl-1.16.0-cp312-cp312-musllinux_1_2_x86_64.whl", hash = "sha256:1a5cf32539373ff39d97723e39a9283a7277cbf1224f7aef0c56c9598b6486c3", size = 355746 },
    { url = "https://files.pythonhosted.org/packages/d9/a6/a2098bf3f09d38eb540b2b192e180d9d41c2ff64b692783db2188f0a55e3/yarl-1.16.0-cp312-cp312-win32.whl", hash = "sha256:a5b6c09b9b4253d6a208b0f4a2f9206e511ec68dce9198e0fbec4f160137aa67", size = 82675 },
    { url = "https://files.pythonhosted.org/packages/ed/a6/0a54b382cfc336e772b72681d6816a99222dc2d21876e649474973b8d244/yarl-1.16.0-cp312-cp312-win_amd64.whl", hash = "sha256:1208ca14eed2fda324042adf8d6c0adf4a31522fa95e0929027cd487875f0240", size = 88986 },
    { url = "https://files.pythonhosted.org/packages/fb/f7/87a32867ddc1a9817018bfd6109ee57646a543acf0d272843d8393e575f9/yarl-1.16.0-py3-none-any.whl", hash = "sha256:e6980a558d8461230c457218bd6c92dfc1d10205548215c2c21d79dc8d0a96f3", size = 43746 },
]
