# Copyright (c) 2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.

# GPU family of target platform. Supported values: tegra, non-tegra
riva_target_gpu_family="non-tegra"

# Name of tegra platform that is being used. Supported tegra platforms: orin, xavier
riva_tegra_platform="orin"

# Enable or Disable Riva Services
service_enabled_asr=true
service_enabled_nlp=false
service_enabled_tts=false
service_enabled_nmt=false

# Enable Riva Enterprise
# If enrolled in Enterprise, enable Riva Enterprise by setting configuration
# here. You must explicitly acknowledge you have read and agree to the EULA.
# RIVA_API_KEY=<ngc api key>
# RIVA_API_NGC_ORG=<ngc organization>
# RIVA_EULA=accept

# Language code to fetch models of a specify language
# Currently only ASR supports languages other than English
# Supported language codes: ar-AR, en-US, en-GB, de-DE, es-ES, es-US, fr-FR, hi-IN, it-IT, ja-JP, ru-RU, ko-KR, pt-BR, zh-CN
# for any language other than English, set service_enabled_nlp and service_enabled_tts to False
# for multiple languages enter space separated language codes.
language_code=("en-US")

# ASR acoustic model architecture
# Supported values are: conformer, conformer_unified (ja-JP only), conformer_xl (en-US + amd64 only), citrinet_1024, citrinet_256 (en-US + arm64 only), jasper (en-US + amd64 only), quartznet (en-US + amd64 only)
asr_acoustic_model=("conformer")

# Specify one or more GPUs to use
# specifying more than one GPU is currently an experimental feature, and may result in undefined behaviours.
gpus_to_use="device=0"

# Specify the encryption key to use to deploy models
MODEL_DEPLOY_KEY="tlt_encode"

# Locations to use for storing models artifacts
#
# If an absolute path is specified, the data will be written to that location
# Otherwise, a docker volume will be used (default).
#
# riva_init.sh will create a `rmir` and `models` directory in the volume or
# path specified.
#
# RMIR ($riva_model_loc/rmir)
# Riva uses an intermediate representation (RMIR) for models
# that are ready to deploy but not yet fully optimized for deployment. Pretrained
# versions can be obtained from NGC (by specifying NGC models below) and will be
# downloaded to $riva_model_loc/rmir by `riva_init.sh`
#
# Custom models produced by NeMo or TLT and prepared using riva-build
# may also be copied manually to this location $(riva_model_loc/rmir).
#
# Models ($riva_model_loc/models)
# During the riva_init process, the RMIR files in $riva_model_loc/rmir
# are inspected and optimized for deployment. The optimized versions are
# stored in $riva_model_loc/models. The riva server exclusively uses these
# optimized versions.
riva_model_loc="riva-model-repo"

if [[ $riva_target_gpu_family == "tegra" ]]; then
    riva_model_loc="`pwd`/model_repository"
fi

# The default RMIRs are downloaded from NGC by default in the above $riva_rmir_loc directory
# If you'd like to skip the download from NGC and use the existing RMIRs in the $riva_rmir_loc
# then set the below $use_existing_rmirs flag to true. You can also deploy your set of custom
# RMIRs by keeping them in the riva_rmir_loc dir and use this quickstart script with the
# below flag to deploy them all together.
use_existing_rmirs=false

# Ports to expose for Riva services
riva_speech_api_port="50051"

# NGC orgs
riva_ngc_org="nvidia"
riva_ngc_team="riva"
riva_ngc_image_version="2.12.1"
riva_ngc_model_version="2.12.0"

# Pre-built models listed below will be downloaded from NGC. If models already exist in $riva-rmir
# then models can be commented out to skip download from NGC

########## ASR MODELS ##########

models_asr=()

for lang_code in ${language_code[@]}; do
    modified_lang_code="${lang_code/-/_}"
    modified_lang_code=${modified_lang_code,,}

    # Setting default Conformer Mandarin and Japanese models to greedy decoder due to high high latency in os2s.
    decoder=""
    if [[ ${asr_acoustic_model} == "conformer" ]]; then
      if [[ ${lang_code} == "zh-CN" ]]; then
          decoder="_gre"
      fi
    fi

    if [[ ${asr_acoustic_model} == "conformer_xl" && ${lang_code} != "en-US" ]]; then
      echo "Conformer-XL acoustic model is only available for language code en-US."
      exit 1
    fi

    if [[ ${asr_acoustic_model} == "conformer_unified" && ${lang_code} != "ja-JP" ]]; then
      echo "Unified Conformer acoustic model is only available for language code ja-JP."
      exit 1
    fi

    if [[ $riva_target_gpu_family  == "tegra" ]]; then

      if [[ ${asr_acoustic_model} == "jasper" || \
            ${asr_acoustic_model} == "quartznet" || \
            ${asr_acoustic_model} == "conformer_xl" ]]; then
          echo "Conformer-XL, Jasper and Quartznet models are not available for arm64 architecture"
          exit 1
      fi

      if [[ ${asr_acoustic_model} == "citrinet_256" && ${lang_code} != "en-US" ]]; then
        echo "For arm64 architecture, citrinet_256 acoustic model is only available for language code en-US."
        exit 1
      fi

      models_asr+=(
      ### Streaming w/ CPU decoder, best latency configuration
          "${riva_ngc_org}/${riva_ngc_team}/models_asr_${asr_acoustic_model}_${modified_lang_code}_str:${riva_ngc_model_version}-${riva_target_gpu_family}-${riva_tegra_platform}"

      ### Offline w/ CPU decoder
      #    "${riva_ngc_org}/${riva_ngc_team}/rmir_asr_${asr_acoustic_model}_${modified_lang_code}_ofl${decoder}:${riva_ngc_model_version}"
      )
    else

      if [[ ${asr_acoustic_model} != "conformer" && \
            ${asr_acoustic_model} != "conformer_unified" && \
            ${asr_acoustic_model} != "conformer_xl" && \
            ${asr_acoustic_model} != "citrinet_1024" && \
            ${asr_acoustic_model} != "jasper" && \
            ${asr_acoustic_model} != "quartznet" ]]; then
        echo "For amd64 architecture, valid acoustic models are conformer, conformer_unified, conformer_xl, citrinet_1024, jasper and quartznet."
        exit 1
      fi

      if [[ (${asr_acoustic_model} == "jasper" || \
            ${asr_acoustic_model} == "quartznet") && \
            ${lang_code} != "en-US" ]]; then
        echo "jasper and quartznet acoustic models are only available for language code en-US."
        exit 1
      fi

      models_asr+=(
      ### Streaming w/ CPU decoder, best latency configuration
          "${riva_ngc_org}/${riva_ngc_team}/rmir_asr_${asr_acoustic_model}_${modified_lang_code}_str${decoder}:${riva_ngc_model_version}"

      ### Streaming w/ CPU decoder, best throughput configuration
      #    "${riva_ngc_org}/${riva_ngc_team}/rmir_asr_${asr_acoustic_model}_${modified_lang_code}_str_thr${decoder}:${riva_ngc_model_version}"

      ### Offline w/ CPU decoder
          "${riva_ngc_org}/${riva_ngc_team}/rmir_asr_${asr_acoustic_model}_${modified_lang_code}_ofl${decoder}:${riva_ngc_model_version}"
      )
    fi

    ### Punctuation model
    if [[ ${asr_acoustic_model} != "conformer_unified" ]]; then
      if [[ $riva_target_gpu_family == "tegra" ]]; then
        models_asr+=(
            "${riva_ngc_org}/${riva_ngc_team}/models_nlp_punctuation_bert_base_${modified_lang_code}:${riva_ngc_model_version}-${riva_target_gpu_family}-${riva_tegra_platform}"
        )
      else
        models_asr+=(
            "${riva_ngc_org}/${riva_ngc_team}/rmir_nlp_punctuation_bert_base_${modified_lang_code}:${riva_ngc_model_version}"
        )
      fi
    fi
done

### Speaker diarization model
models_asr+=(
#    "${riva_ngc_org}/${riva_ngc_team}/rmir_diarizer_offline:${riva_ngc_model_version}"
)

########## NLP MODELS ##########

if [[ $riva_target_gpu_family == "tegra" ]]; then
  models_nlp=(
  ### BERT Base Intent Slot model for misty domain fine-tuned on weather, smalltalk/personality, poi/map datasets.
      "${riva_ngc_org}/${riva_ngc_team}/models_nlp_intent_slot_misty_bert_base:${riva_ngc_model_version}-${riva_target_gpu_family}-${riva_tegra_platform}"

  ### DistilBERT Intent Slot model for misty domain fine-tuned on weather, smalltalk/personality, poi/map datasets.
  #    "${riva_ngc_org}/${riva_ngc_team}/models_nlp_intent_slot_misty_distilbert:${riva_ngc_model_version}-${riva_target_gpu_family}-${riva_tegra_platform}"
  )
else
  models_nlp=(
  ### Bert base Punctuation model
      "${riva_ngc_org}/${riva_ngc_team}/rmir_nlp_punctuation_bert_base_en_us:${riva_ngc_model_version}"

  ### BERT base Named Entity Recognition model fine-tuned on GMB dataset with class labels LOC, PER, ORG etc.
      "${riva_ngc_org}/${riva_ngc_team}/rmir_nlp_named_entity_recognition_bert_base:${riva_ngc_model_version}"

  ### BERT Base Intent Slot model fine-tuned on weather dataset.
      "${riva_ngc_org}/${riva_ngc_team}/rmir_nlp_intent_slot_bert_base:${riva_ngc_model_version}"

  ### BERT Base Question Answering model fine-tuned on Squad v2.
      "${riva_ngc_org}/${riva_ngc_team}/rmir_nlp_question_answering_bert_base:${riva_ngc_model_version}"

  ### Megatron345M Question Answering model fine-tuned on Squad v2.
  #    "${riva_ngc_org}/${riva_ngc_team}/rmir_nlp_question_answering_megatron:${riva_ngc_model_version}"

  ### Bert base Text Classification model fine-tuned on 4class (weather, meteorology, personality, nomatch) domain model.
      "${riva_ngc_org}/${riva_ngc_team}/rmir_nlp_text_classification_bert_base:${riva_ngc_model_version}"
  )
fi

########## TTS MODELS ##########

if [[ $riva_target_gpu_family == "tegra" ]]; then
  models_tts=(
  ### This model has been trained with energy conditioning and International Phonetic Alphabet (IPA) for inference and training.
      "${riva_ngc_org}/${riva_ngc_team}/models_tts_fastpitch_hifigan_en_us_ipa:${riva_ngc_model_version}-${riva_target_gpu_family}-${riva_tegra_platform}"

    #"${riva_ngc_org}/${riva_ngc_team}/models_tts_radtts_hifigan_en_us_ipa:${riva_ngc_model_version}-${riva_target_gpu_family}-${riva_tegra_platform}"

  ### This model uses the ARPABET for inference and training.
  #    "${riva_ngc_org}/${riva_ngc_team}/models_tts_fastpitch_hifigan_en_us:${riva_ngc_model_version}-${riva_target_gpu_family}-${riva_tegra_platform}"
  )
else
  models_tts=(
  ### These models have been trained with energy conditioning and use the International Phonetic Alphabet (IPA) for inference and training.
      "${riva_ngc_org}/${riva_ngc_team}/rmir_tts_fastpitch_hifigan_en_us_ipa:${riva_ngc_model_version}"
      "${riva_ngc_org}/${riva_ngc_team}/rmir_tts_radtts_hifigan_en_us_ipa:${riva_ngc_model_version}"

  ### This model uses the ARPABET for inference and training.
  #    "${riva_ngc_org}/${riva_ngc_team}/rmir_tts_fastpitch_hifigan_en_us:${riva_ngc_model_version}"
  )
fi

######### NMT models ###############

# Only models specified here get loaded, commented models (preceded with #) are skipped.
# models follow Source language _ One or more target languages model architecture
# e.g., rmir_de_en_24x6 is a German to English 24x6 bilingual model

models_nmt=(
  ###### Bilingual models
  #"${riva_ngc_org}/${riva_ngc_team}/rmir_nmt_en_de_24x6:${riva_ngc_model_version}"
  #"${riva_ngc_org}/${riva_ngc_team}/rmir_nmt_en_es_24x6:${riva_ngc_model_version}"
  #"${riva_ngc_org}/${riva_ngc_team}/rmir_nmt_en_zh_24x6:${riva_ngc_model_version}"
  #"${riva_ngc_org}/${riva_ngc_team}/rmir_nmt_en_ru_24x6:${riva_ngc_model_version}"
  #"${riva_ngc_org}/${riva_ngc_team}/rmir_nmt_en_fr_24x6:${riva_ngc_model_version}"
  #"${riva_ngc_org}/${riva_ngc_team}/rmir_nmt_de_en_24x6:${riva_ngc_model_version}"
  #"${riva_ngc_org}/${riva_ngc_team}/rmir_nmt_es_en_24x6:${riva_ngc_model_version}"
  #"${riva_ngc_org}/${riva_ngc_team}/rmir_nmt_ru_en_24x6:${riva_ngc_model_version}"
  #"${riva_ngc_org}/${riva_ngc_team}/rmir_nmt_zh_en_24x6:${riva_ngc_model_version}"
  #"${riva_ngc_org}/${riva_ngc_team}/rmir_nmt_fr_en_24x6:${riva_ngc_model_version}"

  ###### Multilingual models
  #"${riva_ngc_org}/${riva_ngc_team}/rmir_nmt_en_deesfr_24x6:${riva_ngc_model_version}"
  #"${riva_ngc_org}/${riva_ngc_team}/rmir_nmt_en_deesfr_12x2:${riva_ngc_model_version}"
  #"${riva_ngc_org}/${riva_ngc_team}/rmir_nmt_deesfr_en_24x6:${riva_ngc_model_version}"
  #"${riva_ngc_org}/${riva_ngc_team}/rmir_nmt_deesfr_en_12x2:${riva_ngc_model_version}"

  ###### Megatron models
  #"${riva_ngc_org}/${riva_ngc_team}/rmir_megatronnmt_any_en_500m:${riva_ngc_model_version}"
  #"${riva_ngc_org}/${riva_ngc_team}/rmir_megatronnmt_en_any_500m:${riva_ngc_model_version}"
)

NGC_TARGET=${riva_ngc_org}
if [[ ! -z ${riva_ngc_team} ]]; then
  NGC_TARGET="${NGC_TARGET}/${riva_ngc_team}"
else
  team="\"\""
fi

# Specify paths to SSL Key and Certificate files to use TLS/SSL Credentials for a secured connection.
# If either are empty, an insecure connection will be used.
# Stored within container at /ssl/servert.crt and /ssl/server.key
# Optional, one can also specify a root certificate, stored within container at /ssl/root_server.crt
ssl_server_cert=""
ssl_server_key=""
ssl_root_cert=""

# define docker images required to run Riva
image_speech_api="nvcr.io/${NGC_TARGET}/riva-speech:${riva_ngc_image_version}"

# define docker images required to setup Riva
image_init_speech="nvcr.io/${NGC_TARGET}/riva-speech:${riva_ngc_image_version}-servicemaker"

# daemon names
riva_daemon_speech="riva-speech"
if [[ $riva_target_gpu_family != "tegra" ]]; then
    riva_daemon_client="riva-client"
fi