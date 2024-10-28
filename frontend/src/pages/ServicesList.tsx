import React, { useEffect, useState } from 'react';
import Header from '../components/Header';
import ServiceBox from '../components/ServiceBox';
import { styled } from 'styled-components';

interface ManutencaoMaquina {
  _id: string;
  ordem_servico: Ordemserv[];
}

interface Ordemserv {
  problema: string;
  equipamentos_necessarios: Equipamento[];
  prioridade: string;
  solucao: {
    passos: Passo[];
    observacoes: string[];
    referencias: string[];
  };
}

interface Equipamento {
  nome: string;
  sap_code: string;
  quantidade: number;
}

interface Passo {
  ordem: number;
  duracao: string;
  descricao: string;
  justificativa: string;
  medidas_seguranca: string[];
}

const LinkDecor = styled.a`
  text-decoration: none;
  color: inherit;
`;

const ServicesDisplay = styled.div`
  display: flex;
  flex-wrap: wrap;
`;

function ServicesList() {
  const [data, setdata] = useState<ManutencaoMaquina[]>([]);
  useEffect(() => {
    const fetchData = async () => {
      const data = await fetch('http://localhost:8000/getServices');
      const datajs = await data.json();
      setdata(datajs);
      console.log(datajs);
    };

    // call the function
    fetchData()
      // make sure to catch any error
      .catch(console.error);
  }, []);

  return (
    <>
      <Header></Header>
      <ServicesDisplay>
        {data?.map((service) => (
          <LinkDecor href={`/service/${service._id}`}>
            <ServiceBox title={service.ordem_servico[0].problema}>
              <p style={{ color: 'red' }}>
                prioridade {service.ordem_servico[0].prioridade}
              </p>
              {service.ordem_servico[0].equipamentos_necessarios?.map(
                (tool) => (
                  <p>
                    {tool.sap_code} - {tool.nome}
                  </p>
                )
              )}
            </ServiceBox>
          </LinkDecor>
        ))}
      </ServicesDisplay>
    </>
  );
}

export default ServicesList;
