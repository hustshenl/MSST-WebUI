import gradio as gr

from tools.webUI.constant import *
from tools.webUI.utils import i18n, get_device, load_selected_model, select_folder, open_folder, stop_all_thread
from tools.webUI.init import init_selected_model, init_selected_msst_model
from inference.msst import (
    run_inference_single, 
    run_multi_inference, 
    update_selected_model, 
    update_inference_settings, 
    save_config, reset_config
)

def msst(webui_config):
    gr.Markdown(value=i18n("MSST音频分离原项目地址: [https://github.com/ZFTurbo/Music-Source-Separation-Training](https://github.com/ZFTurbo/Music-Source-Separation-Training)"))
    with gr.Row():
        select_model_type = gr.Dropdown(label=i18n("选择模型类型"), choices=["vocal_models", "multi_stem_models", "single_stem_models"], value=webui_config['inference']['model_type'] if webui_config['inference']['model_type'] else None, interactive=True, scale=1)
        selected_model = gr.Dropdown(label=i18n("选择模型"),choices=load_selected_model(),value=webui_config['inference']['selected_model'] if webui_config['inference']['selected_model'] else None,interactive=True,scale=4)
    with gr.Row():
        gpu_id = gr.CheckboxGroup(label=i18n("选择使用的GPU"),choices=get_device(),value=webui_config['inference']['device'] if webui_config['inference']['device'] else get_device()[0],interactive=True)
        output_format = gr.Radio(label=i18n("输出格式"),choices=["wav", "mp3", "flac"],value=webui_config['inference']['output_format'] if webui_config['inference']['output_format'] else "wav", interactive=True)
    with gr.Row():
        with gr.Column():
            force_cpu = gr.Checkbox(label=i18n("使用CPU (注意: 使用CPU会导致速度非常慢) "),value=webui_config['inference']['force_cpu'] if webui_config['inference']['force_cpu'] else False,interactive=True)
            use_tta = gr.Checkbox(label=i18n("使用TTA (测试时增强), 可能会提高质量, 但速度稍慢"),value=webui_config['inference']['use_tta'] if webui_config['inference']['use_tta'] else False,interactive=True)
        with gr.Column():
            extract_instrumental_label, instrumental_only_label = init_selected_msst_model()
            extract_instrumental = gr.Checkbox(label=extract_instrumental_label,value=webui_config['inference']['extract_instrumental'] if webui_config['inference']['extract_instrumental'] else False,interactive=True)
            instrumental_only = gr.Checkbox(label=instrumental_only_label,value=webui_config['inference']['instrumental_only'] if webui_config['inference']['instrumental_only'] else False,interactive=True)
    with gr.Tabs():
        with gr.TabItem(label=i18n("输入音频")):
            single_audio = gr.Files(label=i18n("上传一个或多个音频文件"), type="filepath")
        with gr.TabItem(label=i18n("输入文件夹")):
            with gr.Row():
                multiple_audio_input = gr.Textbox(label=i18n("输入目录"),value=webui_config['inference']['multiple_audio_input'] if webui_config['inference']['multiple_audio_input'] else "input/",interactive=True,scale=3)
                select_multi_input_dir = gr.Button(i18n("选择文件夹"), scale=1)
                open_multi_input_dir = gr.Button(i18n("打开文件夹"), scale=1)
    with gr.Row():
        store_dir = gr.Textbox(label=i18n("输出目录"),value=webui_config['inference']['store_dir'] if webui_config['inference']['store_dir'] else "results/",interactive=True,scale=3)
        select_store_btn = gr.Button(i18n("选择文件夹"), scale=1)
        open_store_btn = gr.Button(i18n("打开文件夹"), scale=1)
    with gr.Accordion(i18n("推理参数设置, 不同模型之间参数相互独立 (一般不需要动) "), open=False):
        gr.Markdown(value=i18n("只有在点击保存后才会生效。参数直接写入配置文件, 无法撤销。假如不知道如何设置, 请保持默认值。<br>请牢记自己修改前的参数数值, 防止出现问题以后无法恢复。请确保输入正确的参数, 否则可能会导致模型无法正常运行。<br>假如修改后无法恢复, 请点击``重置``按钮, 这会使得配置文件恢复到默认值。"))
        if webui_config['inference']['selected_model']:
            batch_size_number, dim_t_number, num_overlap_number = init_selected_model()
        else:
            batch_size_number, dim_t_number, num_overlap_number = i18n("请先选择模型"), i18n("请先选择模型"), i18n("请先选择模型")
        with gr.Row():
            batch_size = gr.Number(label=i18n("batch_size: 批次大小, 一般不需要改"), value=batch_size_number)
            dim_t = gr.Number(label=i18n("dim_t: 时序维度大小, 一般不需要改 (部分模型没有此参数)"), value=dim_t_number)
            num_overlap = gr.Number(label=i18n("num_overlap: 窗口重叠长度, 数值越小速度越快, 但会牺牲效果"), value=num_overlap_number)
        normalize = gr.Checkbox(label=i18n("normalize: 是否对音频进行归一化处理 (部分模型没有此参数)"), value=False, interactive=False)
        reset_config_button = gr.Button(i18n("重置配置"), variant="secondary")
        save_config_button = gr.Button(i18n("保存配置"), variant="primary")
    with gr.Row():
        inference_single = gr.Button(i18n("输入音频分离"), variant="primary")
        inference_multiple = gr.Button(i18n("输入文件夹分离"), variant="primary")
    with gr.Row():
        output_message = gr.Textbox(label="Output Message", scale=4)
        stop_thread = gr.Button(i18n("强制停止"), scale=1)

    inference_single.click(fn=run_inference_single,inputs=[selected_model, single_audio, store_dir, extract_instrumental, gpu_id, output_format, force_cpu, use_tta, instrumental_only],outputs=output_message)
    inference_multiple.click(fn=run_multi_inference, inputs=[selected_model, multiple_audio_input, store_dir, extract_instrumental, gpu_id, output_format, force_cpu, use_tta, instrumental_only],outputs=output_message)
    select_model_type.change(fn=update_selected_model, inputs=[select_model_type], outputs=[selected_model])
    selected_model.change(fn=update_inference_settings,inputs=[selected_model],outputs=[batch_size, dim_t, num_overlap, normalize, extract_instrumental, instrumental_only])
    save_config_button.click(fn=save_config,inputs=[selected_model, batch_size, dim_t, num_overlap, normalize],outputs=output_message)
    reset_config_button.click(fn=reset_config,inputs=[selected_model],outputs=output_message)
    select_store_btn.click(fn=select_folder, outputs=store_dir)
    open_store_btn.click(fn=open_folder, inputs=store_dir)
    select_multi_input_dir.click(fn=select_folder, outputs=multiple_audio_input)
    open_multi_input_dir.click(fn=open_folder, inputs=multiple_audio_input)
    stop_thread.click(fn=stop_all_thread)