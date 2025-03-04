from datetime import datetime


def decode(raw_data):
    try:
        import chardet
        detection = chardet.detect(raw_data)
        encoding = detection['encoding'] if detection['confidence'] > 0.7 else 'utf-8'
        data = raw_data.decode(encoding, errors='replace')
    except Exception as e:
        # 多编码尝试
        for codec in ['utf-8', 'gbk', 'gb18030', 'big5']:
            try:
                data = raw_data.decode(codec, errors='replace')
                break
            except:
                continue
        else:
            data = raw_data.decode('utf-8', errors='replace')
    finally:
        return data

def lord_model(title='hello world!' , model_content=''):
    if model_content:
        source_code = model_content
        model_content = source_code.replace('$TIME$', datetime.now().strftime("%Y-%m-%d %H:%M:%S")).replace(
            '$TITLE$', title)
    return model_content